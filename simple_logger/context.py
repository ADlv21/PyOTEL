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

def send_to_api(message: str, trace_id: Optional[str] = None, log_type: str = "print", log_level: str = "INFO"):
    """Send a message to the API endpoint without waiting for response."""
    try:
        # Create payload
        trace_id = trace_id or "default"
        current_time = time.time()  # Get current epoch timestamp
        payload = {
            "data": {
                "messages": [{
                    "message": message,
                    "type": log_type,
                    "level": log_level,
                    "timestamp": current_time
                }],
                "trace_id": trace_id,
                "timestamp": current_time
            }
        }
        
        # Send in a separate thread without waiting
        def send_request():
            try:
                requests.post(
                    "http://0.0.0.0:8080",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=1.0
                )
            except Exception as e:
                # Log but don't propagate the error
                logging.error(f"Error sending log to API: {str(e)}")
        
        # Start thread and don't wait for it
        thread = threading.Thread(target=send_request, daemon=True)
        thread.start()
    except Exception as e:
        # Catch all exceptions to ensure logging doesn't affect main program
        logging.error(f"Error preparing log for API: {str(e)}")

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
            # Map Python log levels to standard log levels
            level_map = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO", 
                logging.WARNING: "WARN",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "FATAL"
            }
            log_level = level_map.get(record.levelno, "INFO")
            send_to_api(message, trace_id, "log", log_level)
        except Exception as e:
            logging.error(f"Error in APILogHandler: {str(e)}")
            self.handleError(record)

def traced_print(*args, **kwargs):
    """Print function that prepends the current trace ID if available and sends to API."""
    try:
        trace_id = trace_id_var.get()
        message = " ".join(str(arg) for arg in args)
        
        # Extract log level if provided in kwargs
        log_level = kwargs.pop("log_level", "INFO")
        
        # Print to console
        if trace_id:
            original_print(f"[trace_id: {trace_id}]", *args, **kwargs)
        else:
            original_print(*args, **kwargs)
        
        # Send to API without waiting
        send_to_api(message, trace_id, "print", log_level)
    except Exception as e:
        # Ensure print never fails
        original_print(*args, **kwargs)
        logging.error(f"Error in traced_print: {str(e)}")

def setup_traced_print():
    """Set up the print function to include trace IDs and send to API."""
    builtins.print = traced_print
    
    # Add API handler to root logger
    try:
        root_logger = logging.getLogger()
        api_handler = APILogHandler()
        root_logger.addHandler(api_handler)
    except Exception as e:
        logging.error(f"Error setting up API log handler: {str(e)}")

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