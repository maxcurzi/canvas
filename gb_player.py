import numpy as np
from PIL import Image
from pyboy import PyBoy

from dbmanager import DbManager
from utils import TimedCall


class GameboyPlayer:
    def __init__(self, dbm: DbManager, rom_path: str) -> None:
        self.dbm = dbm
        self.rom_path = rom_path

    def _expand2square(self, pil_img, background_color):
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

    def play_gb(self):
        video_updater = TimedCall(func=self.dbm.update, interval=0.1)

        frames_dict = {}
        i = 0
        while True:
            with PyBoy(self.rom_path) as pyboy:
                while not pyboy.tick():
                    i += 1

                    # time.sleep(4 / 60)
                    pil_image = pyboy.screen_image().convert("P")
                    im_new = self._expand2square(pil_image, (0, 0, 0))
                    frames = [np.asarray(im_new)]
                    # im_new.save("screenshot_square.png")
                    for i_frame, frame in enumerate(frames):
                        frames_dict[i_frame] = {}
                        for j, v in enumerate(frame.flatten()):
                            frames_dict[i_frame][j] = v
                    if i % 60 == 0:
                        video_updater.update(frames_dict[0])
