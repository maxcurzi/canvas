import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path
import time
from typing import Callable

cred = credentials.Certificate(
    Path(
        # "backend",
        # "firebase",
        "secret",
        "canvas-f06e2-firebase-adminsdk-fakna-1688133a0f.json",
    )
)
firebase_admin.initialize_app(cred)


class DbManager:
    def __init__(self, url=None):
        self._pixel_ref = db.reference(
            "/pixels",
            url=url,
        )
        self._req_ref = db.reference(
            "/requests",
            url=url,
        )
        self.i = 0
        self.img_size = 48

    def update(self, new_data: dict | None):
        pixel_data = self._pixel_ref.get()
        if not isinstance(pixel_data, list):
            return
        i = self.i
        new_pixel_data = pixel_data
        new_dict = {}
        if new_data is not None:
            for k, v in new_data.items():
                new_dict[k] = int(v)  # % 13)
        else:
            for j in range(len(new_pixel_data)):
                new_dict[j] = i % 8
        self._pixel_ref.update(new_dict)
        i += 1
        i %= self.img_size * self.img_size
        self.i = i

    def requests(self):
        data = self._req_ref.get()
        return data


class TimedCall:
    def __init__(self, func: Callable, interval: float = 1) -> None:
        self._interval = interval
        self._t_last = time.perf_counter()
        self._func = func

    def update(self):
        if time.perf_counter() - self._t_last > self._interval:
            self._func()
            self._t_last += self._interval


# play_video(dbm)


def manage_requests(dbm: DbManager):
    # Use a transaction to read and delete all the data
    ref = dbm._req_ref
    # Read the data
    data = ref.get()
    pixel_data = dbm._pixel_ref.get()
    # print(pixel_data)
    # iterate over the keys
    new_pixels = {}
    if isinstance(data, dict):
        for key in data.keys():
            req = ref.child(key).get()
            if isinstance(req, dict):
                new_pixels[req["pixelReq"]] = pixel_data[req["pixelReq"]] + 1
                new_pixels[req["pixelReq"]] %= 8

            ref.child(key).delete()
        dbm._pixel_ref.update(new_pixels)
        # Now you can work with the requests data


from functools import partial


def serve_requests(dbm):
    # req_manager = partial(manage_requests, dbm)
    request_server = TimedCall(lambda: manage_requests(dbm), interval=0.2)
    while True:
        request_server.update()
        time.sleep(0.01)


if __name__ == "__main__":

    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    serve_requests(dbm)
