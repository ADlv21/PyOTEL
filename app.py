import builtins
import time
import uuid
import json
import contextvars
from fastapi import FastAPI, Request, HTTPException
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

trace_id_var = contextvars.ContextVar("trace_id", default=None)

original_print = builtins.print

def traced_print(*args, **kwargs):
    trace_id = trace_id_var.get()
    if trace_id:
        original_print(f"[trace_id: {trace_id}]", *args, **kwargs)
    else:
        original_print(*args, **kwargs)

# Monkey patch built-in print
builtins.print = traced_print

class SimpleLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        cookies = dict(request.cookies)
        
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)

        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)

        start_time = time.time()
        body_bytes = await request.body()
        body = body_bytes.decode("utf-8") if body_bytes else None

        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)

        response.headers["X-Trace-Id"] = trace_id

        log_data = {
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "status_code": response.status_code,
            "duration_ms": duration,
            "ip" : ip,
            "user_agent" : user_agent,
            "cookies" : cookies
        }
        print(json.dumps(log_data, indent=2))

        return response

# --------------------------------------
# Set up FastAPI with the middleware
# --------------------------------------
app = FastAPI()
app.add_middleware(SimpleLoggerMiddleware)

# --------------------------
# FastAPI app setup
# --------------------------

app = FastAPI()
app.add_middleware(SimpleLoggerMiddleware)

@app.get("/hello")
async def say_hello(name: str = "world"):
    try:
        return await asyncio.wait_for(handle_hello(name), timeout=1.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")

async def handle_hello(name: str):
    print("Inside /hello")
    # Simulate some async work
    await asyncio.sleep(5)  # Adjust/remove this as needed
    return {"message": f"Hello {name}"}

@app.get("/")
def root():
    print("Inside /")
    return {"message": "Hello ADv8"}
