import logging
from fastapi import FastAPI
from simple_logger import SimpleLogger
import uvicorn

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('myapp.log'),
        logging.StreamHandler()
    ]
)

# Create a FastAPI app
app = FastAPI()

# Wrap it with SimpleLogger
app = SimpleLogger(log_request_body=False)(app)

@app.get("/")
def root():
    logger.info('Started')
    logger.error('Finished')
    print("Inside root endpoint")  # This print will include the trace ID
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)