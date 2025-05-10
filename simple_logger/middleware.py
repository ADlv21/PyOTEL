"""
Middleware implementation for SimpleLogger.
"""

import time
import uuid
import json
import aiohttp
import asyncio
from fastapi import FastAPI, Request
from typing import Optional, Dict, Any, Callable, Union
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .context import trace_id_var, setup_traced_print, set_middleware_active

async def api_log_function(log_data: Dict[str, Any]):
    """Custom logging function that sends data to an API endpoint."""
    async with aiohttp.ClientSession() as session:
        try:
            # Convert the entire log data to string
            data_str = json.dumps(log_data)
            payload = {"data": data_str}
            
            async with session.post(
                "http://0.0.0.0:8080",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if not response.ok:
                    print(f"Failed to send log to API. Status: {response.status}")
        except Exception as e:
            print(f"Error sending log to API: {str(e)}")

class SimpleLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request and response information with trace ID.
    """
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list] = None,
        exclude_methods: Optional[list] = None,
        log_request_body: bool = True,
        log_headers: bool = True,
        log_cookies: bool = True,
        log_format: str = "json",
        log_function: Optional[Callable] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.exclude_methods = exclude_methods or []
        self.log_request_body = log_request_body
        self.log_headers = log_headers
        self.log_cookies = log_cookies
        self.log_format = log_format
        self.log_function = log_function or api_log_function  # Use API log function by default

    async def dispatch(self, request: Request, call_next):
        # Check if this path/method should be excluded
        if request.url.path in self.exclude_paths or request.method in self.exclude_methods:
            return await call_next(request)

        # Mark that middleware is active to prevent duplicate logging
        set_middleware_active(True)

        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        cookies = dict(request.cookies) if self.log_cookies else {}

        trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
        trace_id_var.set(trace_id)

        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers) if self.log_headers else {}

        start_time = time.time()

        body = None
        if self.log_request_body:
            try:
                body = "<body reading disabled>"
            except Exception as e:
                body = f"Error reading body: {str(e)}"

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            await self._log_error(
                trace_id, method, path, query_params, headers, body, 
                500, duration, ip, user_agent, cookies, str(e)
            )
            # Reset middleware active flag
            set_middleware_active(False)
            raise

        duration = round((time.time() - start_time) * 1000, 2)

        # Add trace ID to response headers
        response.headers["X-Trace-Id"] = trace_id

        await self._log_request(trace_id, method, path, query_params, headers, body, status_code, duration, ip, user_agent, cookies)

        # Reset middleware active flag
        set_middleware_active(False)
        
        return response

    async def _log_request(
        self, trace_id, method, path, query_params, headers, body, 
        status_code, duration, ip, user_agent, cookies
    ):
        """Log the request information using the configured log function."""
        log_data = {
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "status_code": status_code,
            "duration_ms": duration,
            "ip": ip,
            "user_agent": user_agent,
        }

        if self.log_headers:
            log_data["headers"] = headers

        if self.log_cookies:
            log_data["cookies"] = cookies

        if self.log_request_body and body:
            log_data["body"] = body

        if asyncio.iscoroutinefunction(self.log_function):
            await self.log_function(log_data)
        else:
            self.log_function(log_data)
    
    async def _log_error(self, trace_id, method, path, query_params, headers, body, 
                 status_code, duration, ip, user_agent, cookies, error):
        """Log error information."""
        log_data = {
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "status_code": status_code,
            "duration_ms": duration,
            "ip": ip,
            "user_agent": user_agent,
            "error": error
        }

        if self.log_headers:
            log_data["headers"] = headers

        if self.log_cookies:
            log_data["cookies"] = cookies

        if self.log_request_body and body:
            log_data["body"] = body

        if asyncio.iscoroutinefunction(self.log_function):
            await self.log_function(log_data)
        else:
            self.log_function(log_data)

    def _default_log_function(self, log_data: Dict[str, Any]):
        """Default logging function that prints JSON to stdout."""
        if self.log_format == "json":
            print(json.dumps(log_data, indent=2))
        else:
            trace_id = log_data.get("trace_id")
            method = log_data.get("method")
            path = log_data.get("path")
            status = log_data.get("status_code")
            duration = log_data.get("duration_ms")
            print(f"[trace_id: {trace_id}] [{trace_id}] {method} {path} - {status} ({duration}ms)")


class SimpleLogger:
    """
    Main class that serves as the entry point for the library.
    Provides a wrapper for FastAPI applications similar to CORS middleware.
    """
    def __init__(
        self,
        exclude_paths: Optional[list] = None,
        exclude_methods: Optional[list] = None,
        log_request_body: bool = False,
        log_headers: bool = True,
        log_cookies: bool = True,
        log_format: str = "json",
        log_function: Optional[Callable] = None,
        patch_print: bool = True
    ):
        self.exclude_paths = exclude_paths
        self.exclude_methods = exclude_methods
        self.log_request_body = log_request_body
        self.log_headers = log_headers
        self.log_cookies = log_cookies
        self.log_format = log_format
        self.log_function = log_function or api_log_function  # Use API log function by default
        self.patch_print = patch_print

        # Set up the print function patching
        if patch_print:
            setup_traced_print()

    def __call__(self, app: Union[FastAPI, ASGIApp]) -> Union[FastAPI, ASGIApp]:
        """
        Make the SimpleLogger callable so it can be used as a wrapper.
        Similar to CORS(app) pattern.
        """
        middleware = SimpleLoggerMiddleware(
            app=app,
            exclude_paths=self.exclude_paths,
            exclude_methods=self.exclude_methods,
            log_request_body=self.log_request_body,
            log_headers=self.log_headers,
            log_cookies=self.log_cookies,
            log_format=self.log_format,
            log_function=self.log_function
        )

        if isinstance(app, FastAPI):
            app.add_middleware(SimpleLoggerMiddleware, 
                exclude_paths=self.exclude_paths,
                exclude_methods=self.exclude_methods,
                log_request_body=self.log_request_body,
                log_headers=self.log_headers,
                log_cookies=self.log_cookies,
                log_format=self.log_format,
                log_function=self.log_function
            )
            return app

        # Otherwise, just return the middleware that wraps the app
        return middleware
