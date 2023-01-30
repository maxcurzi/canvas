import asyncio
import websockets
import json


async def hello():
    async with websockets.connect("wss://canvas.maxcurzi.com/service/") as websocket:
        # await websocket.send("Hello world!")
        await websocket.send(json.dumps({"x": 30, "y": 20, "user": "lolo"}))
        await websocket.recv()


asyncio.run(hello())
