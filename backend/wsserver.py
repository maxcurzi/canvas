#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import ssl

import numpy as np
import websockets
from invaders.invaders import Game as SpaceInvaders
from place.place import App as Place

from games.interface import CanvasApp
from utils import PubSub


class InternalError(Exception):
    pass


class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass


class CanvasPlace(Place, CanvasApp):
    pass


# Create and setup logger
logger = logging.getLogger("WS Server")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(name)s | [%(levelname)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Commands (clicks) received
COMMANDS = asyncio.Queue()
# PUB SUB for game state
PUBSUB = PubSub()


async def handler(websocket):
    """Handle connections in a producer/consumer fashion."""
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    _done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def consumer_handler(websocket):
    """Handle incoming messages from the client. It queues users commands"""
    async for message in websocket:
        logger.debug("Received: %s", message)
        await COMMANDS.put(message)


async def producer_handler(websocket):
    """Handle outgoing messages to the client. It sends the game state"""
    async for value in PUBSUB.subscribe():
        await websocket.send(value)


class GameManager:
    def __init__(self, game: CanvasApp) -> None:
        self.game = game

    def read_user_commands(self) -> dict | None:
        try:
            command = COMMANDS.get_nowait()
        except asyncio.QueueEmpty:
            return None

        try:
            command = json.loads(command)
            if isinstance(command, dict) and command.keys() >= {
                "x",
                "y",
                "user",
            }:
                return command
            logger.debug("Received wrong message %s", command)
        except json.decoder.JSONDecodeError as exc:
            raise InternalError(f"Received wrong message {command}") from exc
        return None

    def execute_user_command(self, command: dict):
        self.game.click_at(
            x_pos=command["x"], y_pos=command["y"], owner=command["user"]
        )

    def update_game_state(self):
        self.game.update()

    def game_over(self) -> bool:
        return self.game.finished

    def game_frame(self) -> np.ndarray:
        return np.array(self.game.frame.convert("P")).flatten().tolist()

    def owners(self) -> dict:
        x_max = self.game.resolution[0]
        owners_dict = {}
        owners = self.game.owners_map
        for (x, y), owner in owners.items():
            owners_dict[x * x_max + y] = owner
        return owners

    def broadcast_game_state(self):
        # We send the whole frame every time. Not a great solution for large
        # canvases but ok for small ones.
        message_dict = {"pixels": self.game_frame(), "owners": self.owners()}
        message = json.dumps(message_dict)
        PUBSUB.publish(message)


async def game_producer(framerate: float = 1):
    """Starts the game and broadcasts it to the clients."""
    logger.info("Broadcasting game...")
    while True:
        # Never stop. Just restart a new game afte the previous one is over
        logger.info("Game start")
        game_manager = GameManager(CanvasInvaders(framerate=framerate))
        while not game_manager.game_over():
            try:
                while (command := game_manager.read_user_commands()) is not None:
                    game_manager.execute_user_command(command)
            except InternalError as exc:
                # We catch internal errors and log them but we don't stop the game
                logger.error(exc)

            # Async sleep as much as possible until the next update.
            # This is because pygame updates are blocking and not async
            await asyncio.sleep(max(0.01, 1 / framerate - 0.03))

            game_manager.update_game_state()
            game_manager.broadcast_game_state()


async def main(framerate: float, ws_port: int, ws_address: str, ssl_context):
    """Main function. Starts the websocket server and the game producer. Serves continuously."""
    async with websockets.serve(handler, ws_address, ws_port, ssl=ssl_context):  # type: ignore
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.unsecure:
        # HTTPS/SSL setup
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        SSL_CERT = "/etc/letsencrypt/live/canvas.maxcurzi.com/fullchain.pem"
        SSL_KEY = "/etc/letsencrypt/live/canvas.maxcurzi.com/privkey.pem"
        ssl_context.load_cert_chain(SSL_CERT, keyfile=SSL_KEY)
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
