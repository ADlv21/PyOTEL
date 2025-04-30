"""
Context management for trace IDs and related functionality.
"""

import asyncio
import builtins
import functools
import contextvars
from typing import Optional, Callable, Any, TypeVar, cast

# Context var for trace ID
trace_id_var = contextvars.ContextVar("trace_id", default=None)

# Store the original print function
original_print = builtins.print

def traced_print(*args, **kwargs):
    """Print function that prepends the current trace ID if available."""
    trace_id = trace_id_var.get()
    if trace_id:
        original_print("[trace_id: %s]", trace_id, *args, **kwargs)
    else:
        original_print(*args, **kwargs)

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