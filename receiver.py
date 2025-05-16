from fastapi import FastAPI, Request
import uvicorn
import json
app = FastAPI()


@app.post("/")
async def receive(request: Request):
    data = await request.json()
    with open('data.json', 'a') as f:
        f.write(json.dumps(data) + "\n")
    return {"message": "Data received successfully"}

if __name__ == "__main__":
    uvicorn.run("receiver:app", host="0.0.0.0", port=8080, reload=True)