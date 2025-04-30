"""
Context management for trace IDs and related functionality.
"""

import asyncio
import builtins
import functools
import contextvars
import aiohttp
import json
from typing import Optional, Callable, Any, TypeVar, cast

# Context var for trace ID
trace_id_var = contextvars.ContextVar("trace_id", default=None)

# Store the original print function
original_print = builtins.print

async def send_to_api(message: str, trace_id: Optional[str] = None):
    """Send a message to the API endpoint."""
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "data": json.dumps({
                    "type": "print",
                    "message": message,
                    "trace_id": trace_id
                })
            }
            async with session.post(
                "https://67e5456d18194932a585555c.mockapi.io/ee",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if not response.ok:
                    original_print(f"Failed to send print to API. Status: {response.status}")
        except Exception as e:
            original_print(f"Error sending print to API: {str(e)}")

def traced_print(*args, **kwargs):
    """Print function that prepends the current trace ID if available and sends to API."""
    trace_id = trace_id_var.get()
    message = " ".join(str(arg) for arg in args)
    
    if trace_id:
        original_print(f"[trace_id: {trace_id}]", *args, **kwargs)
    else:
        original_print(*args, **kwargs)
    
    # Send to API in a non-blocking way
    asyncio.create_task(send_to_api(message, trace_id))

def setup_traced_print():
    """Set up the print function to include trace IDs."""
    builtins.print = traced_print

def get_trace_id() -> Optional[str]:
    """Get the current trace ID from the context."""
    return trace_id_var.get()

def set_trace_id(trace_id: str) -> None:
    """Set the trace ID in the current context."""
    trace_id_var.set(trace_id)

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