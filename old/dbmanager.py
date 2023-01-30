from firebase_admin import credentials, db, initialize_app
from utils import TimedCall
import time
import os

initialize_app(
    credential=credentials.Certificate(
        {
            "type": "service_account",
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY")
            .replace("\\n", "\n")
            .replace("'", ""),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
            "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
            "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.environ.get(
                "FIREBASE_AUTH_PROVIDER_X509_CERT_URL"
            ),
            "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
        }
    ),
)


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
