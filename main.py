from fastapi import FastAPI
from simple_logger import SimpleLogger

# Create a FastAPI app
app = FastAPI()

# Wrap it with SimpleLogger
app = SimpleLogger(
    log_request_body=False
)(app)

@app.get("/")
def root():
    print("Inside root endpoint")  # This print will include the trace ID
    return {"message": "Hello World"}