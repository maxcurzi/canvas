from firebase_admin import credentials, db, initialize_app
from pathlib import Path
from utils import TimedCall
import time

import os

print(os.getcwd())
cred = credentials.Certificate(
    Path(
        "secret",
        "canvas-f06e2-firebase-adminsdk-fakna-1688133a0f.json",
    )
)
initialize_app(cred)


class DbManager:
    def __init__(self, url=None, grid_size=64):
        self._pixels_ref = db.reference(
            "/pixels",
            url=url,
        )
        self._owners_ref = db.reference(
            "/owners",
            url=url,
        )
        self._req_ref = db.reference(
            "/requests",
            url=url,
        )
        self.i = 0
        self.grid_size = grid_size

    def update(self, new_pixels: dict | None, new_owners: dict | None):
        pixel_data = self._pixels_ref.get()
        owners_data = self._owners_ref.get()

        if not isinstance(pixel_data, list):
            return
        # Update pixels
        i = self.i
        new_pixel_data = pixel_data
        new_dict = {}
        if new_pixels is not None:
            for k, v in new_pixels.items():
                new_dict[k] = int(v)
        else:
            for j in range(len(new_pixel_data)):
                new_dict[j] = i % 8
        self._pixels_ref.update(new_dict)
        i += 1
        i %= self.grid_size * self.grid_size
        self.i = i

        # if not isinstance(owners_data, dict):
        #     return
        # Update owners
        new_dict = {}
        if new_owners:
            for k, v in new_owners.items():
                new_dict[k[0] * self.grid_size + k[1]] = v
            self._owners_ref.set(new_dict)

    def requests(self):
        return self._req_ref.get()

    def _manage_requests(self):
        ref = self._req_ref
        data = ref.get()
        pixel_data = self._pixels_ref.get()
        new_pixels = {}
        if isinstance(data, dict):
            for key in data.keys():
                req = ref.child(key).get()
                if isinstance(req, dict):
                    if req["pixelReq"] < self.grid_size * self.grid_size:
                        new_pixels[req["pixelReq"]] = pixel_data[req["pixelReq"]] + 1
                        new_pixels[req["pixelReq"]] %= 8

                ref.child(key).delete()
            if new_pixels:
                self._pixels_ref.update(new_pixels)

    def serve_requests(self):
        request_server = TimedCall(lambda: self._manage_requests, interval=0.2)
        while True:
            request_server.update()
            time.sleep(0.01)
