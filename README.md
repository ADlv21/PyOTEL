# SimpleLogger

A Python library for FastAPI that provides request/response logging with trace ID propagation.

## Features

- Wraps FastAPI applications similar to CORS middleware
- Adds trace IDs to all requests
- Propagates trace IDs through the context
- Patches the built-in `print` function to include trace IDs
- Customizable logging formats and functions
- Path and method exclusion options
- Decorators for manually setting trace IDs

## Installation

```bash
pip install simple-logger
```

Or install from source:

```bash
git clone https://github.com/yourusername/simple-logger.git
cd simple-logger
pip install -e .
```

## Quick Start

```python
from fastapi import FastAPI
from simple_logger import SimpleLogger

# Create a FastAPI app
app = FastAPI()

# Wrap it with SimpleLogger
app = SimpleLogger()(app)

@app.get("/")
def root():
    # print statements will automatically include trace IDs
    print("Inside root endpoint")
    return {"message": "Hello World"}
```

## Configuration Options

The `SimpleLogger` constructor accepts the following parameters:

- `exclude_paths`: List of paths to exclude from logging
- `exclude_methods`: List of HTTP methods to exclude from logging
- `log_request_body`: Whether to log the request body (default: True)
- `log_headers`: Whether to log request headers (default: True)
- `log_cookies`: Whether to log cookies (default: True)
- `log_format`: Format for logs, either "json", "simple", or "custom" (default: "json")
- `log_function`: Custom function for logging (default: None)
- `patch_print`: Whether to patch the built-in print function (default: True)

## Advanced Usage

### Custom Logging Function

```python
from fastapi import FastAPI
from simple_logger import SimpleLogger

def my_custom_logger(log_data):
    # Process the log data however you want
    print(f"Custom log: {log_data['method']} {log_data['path']} ({log_data['duration_ms']}ms)")

app = FastAPI()
app = SimpleLogger(
    log_format="custom",
    log_function=my_custom_logger
)(app)
```

### Using with Decorators

```python
from fastapi import FastAPI
from simple_logger import SimpleLogger, with_trace_id, get_trace_id

app = FastAPI()
app = SimpleLogger()(app)

@app.get("/manual-trace")
@with_trace_id("custom-trace-id")
def manual_trace():
    print("This will use a manually set trace ID")
    return {"trace_id": get_trace_id()}  # Will return "custom-trace-id"
```

## Examples

See the `examples` directory for more comprehensive examples:

- `basic_usage.py`: Simple example of using SimpleLogger with FastAPI
- `advanced_usage.py`: Advanced configuration and custom logging

## License

MIT