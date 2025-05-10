from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/")
async def receive(request: Request):
    print(await request.json())
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("receiver:app", host="0.0.0.0", port=8080, reload=True)