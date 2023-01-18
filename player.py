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


from pyboy import PyBoy
from pyboy import WindowEvent
from PIL import Image
import time


def expand2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def play_gb(rom: str):
    video_updater = TimedCall(func=dbm.update, interval=0.1)

    frames_dict = {}
    i = 0
    while True:
        with PyBoy(rom) as pyboy:
            while not pyboy.tick():
                i += 1

                # time.sleep(4 / 60)
                pil_image = pyboy.screen_image().convert("P")
                im_new = expand2square(pil_image, (0, 0, 0))
                frames = [np.asarray(im_new)]
                # im_new.save("screenshot_square.png")
                for i_frame, frame in enumerate(frames):
                    frames_dict[i_frame] = {}
                    for j, v in enumerate(frame.flatten()):
                        frames_dict[i_frame][j] = v
                if i % 60 == 0:
                    video_updater.update(frames_dict[0])


if __name__ == "__main__":

    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    play_video(dbm, Path("assets", "phant_cropped_small.gif"))
    # play_gb("assets/gbroms/Tetris.gb")
