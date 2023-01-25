import subprocess

subprocess.Popen(["python", "player.py"])

from fastapi import FastAPI, HTTPException, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import zmq
import zmq.asyncio

context = zmq.asyncio.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://127.0.0.1:5555")

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/update_pixel/")
async def update_pixel(
    request=Body(None),
):
    x = request["x"]
    y = request["y"]
    user = request["user"]
    print(f"Click received: {x},{y} from {user}")
    if x is None or y is None or user is None:
        raise HTTPException(status_code=400, detail="missing arguments")
    # process the request
    socket.send_json({"x": x, "y": y, "user": user})
    # response = socket.recv_json()
    return {"status": "success"}


@app.options("/update_pixel/")
async def cors_options(request: Request):
    return Response(content={}, headers={"Access-Control-Allow-Origin": "*"})
