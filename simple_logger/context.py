"""
Context management for trace IDs and related functionality.
"""

import asyncio
import builtins
import functools
import contextvars
import requests
import json
import logging
import threading
import time
from typing import Optional, Callable, Any, TypeVar, cast, List, Dict
from collections import defaultdict
from datetime import datetime, timedelta

# Context var for trace ID
trace_id_var = contextvars.ContextVar("trace_id", default=None)

# Context var to track if middleware is handling the request
middleware_active = contextvars.ContextVar("middleware_active", default=False)

# Store the original print function
original_print = builtins.print

# Global variables for batching
log_queue = defaultdict(list)
last_flush = time.time()
BATCH_INTERVAL = 0.5  # seconds
MAX_BATCH_SIZE = 10
flush_thread = None
lock = threading.Lock()

def _flush_logs():
    """Flush logs from the queue to the API."""
    global last_flush
    while True:
        try:
            current_time = time.time()
            if current_time - last_flush >= BATCH_INTERVAL:
                with lock:
                    for trace_id, logs in list(log_queue.items()):
                        if logs:
                            try:
                                payload = {
                                    "data": json.dumps({
                                        "messages": logs,
                                        "trace_id": trace_id,
                                        "type": "batch",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                }
                                
                                # Fire and forget - use a separate thread
                                def send_request():
                                    try:
                                        requests.post(
                                            "http://0.0.0.0:8080",
                                            json=payload,
                                            headers={"Content-Type": "application/json"},
                                            timeout=1.0
                                        )
                                    except Exception:
                                        pass  # Ignore all errors
                                
                                threading.Thread(target=send_request, daemon=True).start()
                                log_queue[trace_id] = []
                            except Exception as e:
                                logging.error(f"Error sending logs to API: {str(e)}")
                    last_flush = current_time
            time.sleep(0.1)  # Small sleep to prevent CPU spinning
        except Exception as e:
            logging.error(f"Error in flush thread: {str(e)}")

def send_to_api(message: str, trace_id: Optional[str] = None, log_type: str = "print"):
    """Send a message to the API endpoint using batching."""
    # Temporarily disable this check to fix the issue
    # if middleware_active.get():
    #     return
        
    global flush_thread
    
    # Start the flush thread if it's not running
    if flush_thread is None or not flush_thread.is_alive():
        flush_thread = threading.Thread(target=_flush_logs, daemon=True)
        flush_thread.start()
    
    # Add message to queue
    trace_id = trace_id or "default"
    with lock:
        log_queue[trace_id].append({
            "message": message,
            "type": log_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # If queue size exceeds max batch size, trigger immediate flush
        if len(log_queue[trace_id]) >= MAX_BATCH_SIZE:
            threading.Thread(target=_flush_logs, daemon=True).start()

class APILogHandler(logging.Handler):
    """Custom logging handler that sends logs to the API."""
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        """Emit a record to the API."""
        try:
            trace_id = trace_id_var.get()
            message = self.format(record)
            send_to_api(message, trace_id, "log")
        except Exception as e:
            logging.error(f"Error in APILogHandler: {str(e)}")
            self.handleError(record)

def traced_print(*args, **kwargs):
    """Print function that prepends the current trace ID if available and sends to API."""
    trace_id = trace_id_var.get()
    message = " ".join(str(arg) for arg in args)
    
    # Print to console
    if trace_id:
        original_print(f"[trace_id: {trace_id}]", *args, **kwargs)
    else:
        original_print(*args, **kwargs)
    
    # Send to API using batching
    send_to_api(message, trace_id, "print")

def setup_traced_print():
    """Set up the print function to include trace IDs and send to API."""
    builtins.print = traced_print
    
    # Add API handler to root logger
    root_logger = logging.getLogger()
    api_handler = APILogHandler()
    root_logger.addHandler(api_handler)

def get_trace_id() -> Optional[str]:
    """Get the current trace ID from the context."""
    return trace_id_var.get()

def set_trace_id(trace_id: str) -> None:
    """Set the trace ID in the current context."""
    trace_id_var.set(trace_id)

def set_middleware_active(active: bool = True) -> None:
    """Set whether middleware is currently handling the request."""
    middleware_active.set(active)

# Generic type for function return
T = TypeVar('T')

def with_trace_id(trace_id: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to run a function with a specific trace ID.
    
    Usage:
    @with_trace_id("my-trace-id")
    def my_function():
        print("This will have the trace ID")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            token = trace_id_var.set(trace_id)
            try:
                return func(*args, **kwargs)
            finally:
                trace_id_var.reset(token)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            token = trace_id_var.set(trace_id)
            try:
                return await func(*args, **kwargs)
            finally:
                trace_id_var.reset(token)
                
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], async_wrapper)
        return cast(Callable[..., T], wrapper)
    
    return decorator