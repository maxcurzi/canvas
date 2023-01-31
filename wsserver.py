#!/usr/bin/env python
import asyncio
import json
import websockets
import numpy as np
from invaders.invaders import Game as SpaceInvaders
from games.interface import CanvasApp
import ssl
import logging
import argparse


class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass


class PubSub:
    def __init__(self):
        self.waiter = asyncio.Future()

    def publish(self, value):
        waiter, self.waiter = self.waiter, asyncio.Future()
        waiter.set_result((value, self.waiter))

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

# HTTPS/SSL setup
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_cert = "/etc/letsencrypt/live/canvas.maxcurzi.com/fullchain.pem"
ssl_key = "/etc/letsencrypt/live/canvas.maxcurzi.com/privkey.pem"
ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

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
        x_max = game.screen.get_width()
        y_max = game.screen.get_height()
        t = 0
        while game._winner() == None:
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
            await asyncio.sleep(max(0, 1 / framerate - 0.03))

            game.update()
            gameframe = np.array(game.frame.convert("P")).flatten().tolist()
            owners_dict = {}
            owners = game.owners_map
            for ((x, y), owner) in owners.items():
                owners_dict[x * x_max + y] = owner
            message_dict = {"pixels": gameframe, "owners": owners_dict}
            message = json.dumps(message_dict)
            PUBSUB.publish(message)


async def main(framerate, wss_port, wss_address):
    async with websockets.serve(handler, wss_address, wss_port, ssl=ssl_context):
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
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(framerate=args.framerate, wss_port=args.port, wss_address=args.address)
    )
