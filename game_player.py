import time

import numpy as np
import zmq
import zmq.asyncio
from invaders.invaders import Game as SpaceInvaders

from games.interface import CanvasApp
from server import DbManager
from utils import TimedCall
import random

context = zmq.asyncio.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://127.0.0.1:5555")
poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)


class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass


async def play_invaders(dbm: DbManager, fps: float = 1, random_game: bool = True):
    video_updater = TimedCall(func=dbm.update, interval=1 / fps)
    while True:
        game = CanvasInvaders(framerate=fps)
        t = 0
        while game._winner() == None:
            game.update()
            frame = np.array(game.frame.convert("P"))
            frames_dict = {}
            for j, v in enumerate(frame.flatten()):
                frames_dict[j] = v
            t += 1
            if random_game:
                if t % 3 == 0:
                    x = random.randint(0, 63)
                    y = random.randint(min(t // 15 + 5, 35), 35)
                    user = "cpu"
                    game.click_at(x, y, user)

                if t % random.randint(3, 12) == 0:
                    x = game.human.rect.centerx
                    y = game.human.rect.centery
                    game.click_at(x, y, user)

            # game.click_at(random.randint(0, 63), random.randint(0, 63), "CPU")
            # Get click events
            # check if there are any messages in the socket
            socks = dict(poller.poll(100))
            if socket in socks:
                while True:
                    # read all the messages in the socket
                    try:
                        request = await socket.recv_json(zmq.NOBLOCK)
                        x, y, user = request["x"], request["y"], request["user"]
                        # update your game state with x, y, and username
                        game.click_at(x, y, user)
                        # socket.send_json({"status": "success"})
                    except zmq.ZMQError as e:
                        if e.errno == zmq.EAGAIN:
                            # no more messages to read
                            break
                            # if e.errno == zmq.EAGAIN:
                            # no more messages to read

            # serve_clicks(dbm=dbm, game=game)
            owners_dict = game.owners_map
            video_updater.update(frames_dict, owners_dict)
            time.sleep(0)
