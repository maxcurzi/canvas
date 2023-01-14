from utils import TimedCall
import time
import numpy as np
from PIL import Image, ImageSequence
from pathlib import Path
from server import DbManager


def get_frames(gif_path: Path) -> list:

    # Open the animated GIF
    frame_pixels = []
    with Image.open(gif_path) as im:

        for i in range(im.n_frames):
            im.seek(i)
            frame = im.convert("L").copy()
            # for i, frame in enumerate(frames):
            frame_pixels.append(np.asarray(frame))
        # # Iterate over the frames of the animation
        # frames = [
        #     np.asarray(frame.copy())
        #     for frame in ImageSequence.Iterator(im.convert("P"))
        # ]
        # # Do something with each frame, e.g. save it to a list
    return frame_pixels


def play_video(dbm: DbManager, gif: Path):
    video_updater = TimedCall(func=dbm.update, interval=0.1)
    frames = get_frames(gif)
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
        time.sleep(0.01)


if __name__ == "__main__":

    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    play_video(dbm, Path("assets", "phant_cropped_small.gif"))
