#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import ssl

import numpy as np
import websockets
import importlib
from games.interface import CanvasApp
from utils import PubSub

from games.game_config import GAMES as GAME_CONFIG


class InternalError(Exception):
    pass



def get_game_class(game_name):
    if game_name not in GAME_CONFIG:
        raise ValueError(f"Unknown game: {game_name}")
    module_path = GAME_CONFIG[game_name]["module"]
    module = importlib.import_module(module_path)
    game_class = getattr(module, "Game")
    # Dynamically create a class that inherits from both the game and CanvasApp
    return type(f"Canvas{game_name.capitalize()}", (game_class, CanvasApp), {})


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
# Store the current game state for new clients to fetch immediately
CURRENT_GAME_STATE = None


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
    global CURRENT_GAME_STATE
    # Send current game state immediately to new clients
    if CURRENT_GAME_STATE:
        await websocket.send(CURRENT_GAME_STATE)
    # Then subscribe to future updates
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
            x=command["x"], y=command["y"], owner=command["user"]
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
        for (y, x), owner in owners.items():
            owners_dict[y * x_max + x] = owner
        return owners_dict

    def broadcast_game_state(self):
        # We send the whole frame every time. Not a great solution for large
        # canvases but ok for small ones.
        global CURRENT_GAME_STATE
        message_dict = {"pixels": self.game_frame(), "owners": self.owners()}
        message = json.dumps(message_dict)
        CURRENT_GAME_STATE = message  # Store for new clients
        PUBSUB.publish(message)


async def game_producer(game_class, framerate: float = 1):
    """Starts the game and broadcasts it to the clients."""
    logger.info("Broadcasting game...")
    while True:
        logger.info("Game start")
        game_manager = GameManager(game_class(framerate=framerate))
        while not game_manager.game_over():
            try:
                while (command := game_manager.read_user_commands()) is not None:
                    game_manager.execute_user_command(command)
            except InternalError as exc:
                logger.error(exc)
            await asyncio.sleep(max(0.01, 1 / framerate - 0.03))
            game_manager.update_game_state()
            game_manager.broadcast_game_state()


async def main(game_class, framerate: float, ws_port: int, ws_address: str, ssl_context=None):
    """Main function. Starts the websocket server and the game producer. Serves continuously."""
    async with websockets.serve(handler, ws_address, ws_port, ssl=ssl_context):  # type: ignore
        await game_producer(game_class, framerate=framerate)


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
    parser.add_argument(
        "-g",
        "--game",
        type=str,
        help="Game to run (invaders, place)",
        default="invaders",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.unsecure:
        # HTTPS/SSL setup
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        import os
        SSL_CERT = os.environ.get("SSL_CERT_PATH", "cert.pem")
        SSL_KEY = os.environ.get("SSL_KEY_PATH", "key.pem")
        ssl_context.load_cert_chain(SSL_CERT, keyfile=SSL_KEY)
    else:
        ssl_context = None
    # Dynamically get the game class
    game_class = get_game_class(args.game)
    asyncio.run(
        main(
            game_class=game_class,
            framerate=args.framerate,
            ws_port=args.port,
            ws_address=args.address,
            ssl_context=ssl_context,
        )
    )
