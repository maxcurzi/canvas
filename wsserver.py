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


# Create logger
logger = logging.getLogger("WS Server")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s | %(name)s | [%(levelname)s]: %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

CONNECTIONS = set()
COMMANDS = asyncio.Queue()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_cert = "/etc/letsencrypt/live/canvas.maxcurzi.com/fullchain.pem"
ssl_key = "/etc/letsencrypt/live/canvas.maxcurzi.com/privkey.pem"
ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)


async def handle_client(websocket):
    CONNECTIONS.add(websocket)
    while True:
        try:
            message = await websocket.recv()
            logger.debug(f"message:{message}")
            await COMMANDS.put(message)
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Closed OK")
            break
        except Exception as e:
            logger.error(f"{e}")
            break


async def broadcast_game(framerate=5):
    logger.info("Broadcasting game...")
    while True:
        logger.info("Game start")
        game = CanvasInvaders(framerate=framerate)
        x_max = game.screen.get_width()
        y_max = game.screen.get_height()
        t = 0
        while game._winner() == None:
            t += 1
            game.update()
            gameframe = np.array(game.frame.convert("P")).flatten().tolist()
            owners_dict = {}
            owners = game.owners_map
            for ((x, y), owner) in owners.items():
                owners_dict[x * x_max + y] = owner
            message_dict = {"pixels": gameframe, "owners": owners_dict}
            message = json.dumps(message_dict)
            websockets.broadcast(CONNECTIONS, message)
            while True:
                try:
                    command = COMMANDS.get_nowait()
                    command = json.loads(command)
                    game.click_at(x=command["x"], y=command["y"], owner=command["user"])
                except asyncio.QueueEmpty:
                    break
                await asyncio.sleep(0)

            await asyncio.sleep(0)


async def main(framerate=1, wss_port=8765, wss_address="canvas.maxcurzi.com"):
    async with websockets.serve(handle_client, wss_address, wss_port, ssl=ssl_context):
        await asyncio.gather(broadcast_game(framerate=framerate))


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
