"""
Advanced example showing customization of SimpleLogger.
"""

import logging
import sys
from fastapi import FastAPI, Request, HTTPException
from simple_logger import SimpleLogger, get_trace_id

# Set up a logger
logger = logging.getLogger("app")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Define a custom log function that uses the Python logging system
def custom_logger(log_data):
    """Custom logging function that includes the trace ID."""
    trace_id = log_data.get("trace_id", "unknown")
    method = log_data.get("method", "")
    path = log_data.get("path", "")
    status = log_data.get("status_code", 0)
    duration = log_data.get("duration_ms", 0)

    # Add trace ID as extra data for the log record
    extra = {"trace_id": trace_id}

    # Log with different levels based on status code
    if status < 400:
        logger.info("%s %s - %d (%dms)", method, path, status, duration, extra=extra)
    elif status < 500:
        logger.warning("%s %s - %d (%dms)", method, path, status, duration, extra=extra)
    else:
        logger.error("%s %s - %d (%dms)", method, path, status, duration, extra=extra)

    # Additionally log the full data at debug level
    logger.debug("Full request data: %s", log_data, extra=extra)

# Create a FastAPI app
app = FastAPI()

# Create a custom middleware class for additional functionality
class CustomMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        # Custom ASGI middleware functionality
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # You could add custom logic here before the request
        return await self.app(scope, receive, send)

# Wrap the app with our middleware first
app = CustomMiddleware(app)

# Now wrap with SimpleLogger with custom configuration
app = SimpleLogger(
    log_format="custom",  # We're using a custom logger
    log_function=custom_logger,
    exclude_paths=["/health", "/metrics"],
    exclude_methods=["OPTIONS"],
    log_request_body=False,
    log_headers=False,  # Don't log headers for privacy
    log_cookies=False,  # Don't log cookies for privacy
)(app)

# Add a custom middleware that demonstrates trace ID access
@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    """Middleware that adds a custom header to all responses."""
    # Access the trace ID that was set by SimpleLogger
    current_trace_id = get_trace_id()
    
    # Process the request
    response = await call_next(request)
    
    # Add custom header
    response.headers["X-App-Version"] = "1.0.0"
    
    # We can use the trace ID here too
    logger.info("Added custom header to response", extra={"trace_id": current_trace_id})
    
    return response

@app.get("/")
def root():
    """Root endpoint."""
    trace_id = get_trace_id()
    logger.info("Root endpoint accessed", extra={"trace_id": trace_id})
    return {"message": "Advanced example", "trace_id": trace_id}

@app.get("/error")
def trigger_error():
    """Endpoint that triggers an error."""
    logger.info("About to raise an exception", extra={"trace_id": get_trace_id()})
    raise HTTPException(status_code=500, detail="Intentional error for testing")

@app.get("/nested")
async def nested_functions():
    """Demonstrates trace ID propagation through nested function calls."""
    return await function_level_1()

async def function_level_1():
    """First level function."""
    logger.info("In function level 1", extra={"trace_id": get_trace_id()})
    return await function_level_2()

async def function_level_2():
    """Second level function."""
    logger.info("In function level 2", extra={"trace_id": get_trace_id()})
    return {"message": "Nested functions with trace ID propagation", "trace_id": get_trace_id()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)