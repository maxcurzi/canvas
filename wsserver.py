#!/usr/bin/env python
import asyncio
import json
import websockets
import numpy as np
from invaders.invaders import Game as SpaceInvaders
from place.place import App as Place
from games.interface import CanvasApp
import ssl
import logging
import argparse


class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass


class CanvasPlace(Place, CanvasApp):
    pass


class PubSub:
    def __init__(self):
        self.waiter = asyncio.Future()

    def publish(self, value):
        waiter, self.waiter = self.waiter, asyncio.Future()
        try:
            waiter.set_result((value, self.waiter))
        except asyncio.exceptions.InvalidStateError as e:
            logger.error(e)

    async def subscribe(self):
        waiter = self.waiter
        while True:
            value, waiter = await waiter
            yield value

    __aiter__ = subscribe


PUBSUB = PubSub()

# Create and setup logger
logger = logging.getLogger("WS Server")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(name)s | [%(levelname)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Commands received
COMMANDS = asyncio.Queue()


async def handler(websocket):
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def consumer_handler(websocket):
    async for message in websocket:
        logger.debug("Received:" + message)
        await COMMANDS.put(message)


async def producer_handler(websocket):
    async for value in PUBSUB.subscribe():
        await websocket.send(value)


async def game_producer(framerate=1):
    logger.info("Broadcasting game...")
    while True:
        logger.info("Game start")
        game = CanvasInvaders(framerate=framerate)
        x_max = game.resolution[0]
        y_max = game.resolution[1]
        t = 0
        while not game.finished:
            t += 1
            while True:
                try:
                    command = COMMANDS.get_nowait()
                    try:
                        command = json.loads(command)
                        if isinstance(command, dict) and command.keys() >= {
                            "x",
                            "y",
                            "user",
                        }:
                            game.click_at(
                                x=command["x"], y=command["y"], owner=command["user"]
                            )
                        else:
                            logger.error(f"Received wrong message:{command}")
                    except json.decoder.JSONDecodeError:
                        logger.error(f"Received wrong message:{command}")
                        break
                except asyncio.QueueEmpty:
                    break
            await asyncio.sleep(max(0.01, 1 / framerate - 0.03))

            game.update()
            gameframe = np.array(game.frame.convert("P")).flatten().tolist()
            owners_dict = {}
            owners = game.owners_map
            for ((x, y), owner) in owners.items():
                owners_dict[x * x_max + y] = owner
            message_dict = {"pixels": gameframe, "owners": owners_dict}
            message = json.dumps(message_dict)
            PUBSUB.publish(message)


async def main(framerate: float, ws_port: int, ws_address: str, ssl_context):
    async with websockets.serve(handler, ws_address, ws_port, ssl=ssl_context):
        await game_producer(framerate=framerate)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--framerate",
        type=float,
        help="Game framerate (directly affects game speed)",
        default=1,
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Websocket port",
        default=8765,
    )
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        help="Websocket address",
        default="canvas.maxcurzi.com",
    )
    parser.add_argument(
        "-u",
        "--unsecure",
        help="Use unsecure web sockets",
        action="store_true",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if not args.unsecure:
        # HTTPS/SSL setup
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_cert = "/etc/letsencrypt/live/canvas.maxcurzi.com/fullchain.pem"
        ssl_key = "/etc/letsencrypt/live/canvas.maxcurzi.com/privkey.pem"
        ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)
    else:
        ssl_context = None
    asyncio.run(
        main(
            framerate=args.framerate,
            ws_port=args.port,
            ws_address=args.address,
            ssl_context=ssl_context,
        )
    )
