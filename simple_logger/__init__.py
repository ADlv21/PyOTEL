"""
SimpleLogger - A FastAPI middleware for request/response logging with trace ID support.

This library provides a clean wrapper for FastAPI applications to add request/response 
logging with trace ID propagation through the application.
"""

from .middleware import SimpleLogger
from .context import get_trace_id, with_trace_id, set_middleware_active, set_trace_id

__all__ = ["SimpleLogger", "get_trace_id", "with_trace_id", "set_middleware_active", "set_trace_id"]
__version__ = "0.1.0"