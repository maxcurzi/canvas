import time
from pathlib import Path

import numpy as np
from PIL import Image

from server import DbManager
from utils import TimedCall


class GifPlayer:
    def __init__(self, dbm: DbManager, gif_path: Path) -> None:
        self.gif_path = gif_path
        self.dbm = dbm

    def play(self):
        video_updater = TimedCall(func=self.dbm.update, interval=0.1)
        frames = self._get_frames()
        frames_dict = {}
        for i_frame, frame in enumerate(frames):
            frames_dict[i_frame] = {}
            for i, v in enumerate(frame.flatten()):
                frames_dict[i_frame][i] = v
        i = 0
        while True:
            if video_updater.update(frames_dict[i]):
                i += 1
                i %= len(frames_dict)
            time.sleep(0)

    def _get_frames(self) -> list:
        frame_pixels = []
        with Image.open(self.gif_path) as im:
            for i in range(im.n_frames):
                im.seek(i)
                frame = im.convert("L").copy()
                frame_pixels.append(np.asarray(frame))
        return frame_pixels
