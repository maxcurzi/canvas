from fastapi import FastAPI
from fastapi.testclient import TestClient
from ...fastapiserver import app

# app = FastAPI()


# @app.get("/")
# async def read_main():
#     return {"msg": "Hello World"}


client = TestClient(app)


def test_update_pixel():
    # response = client.get("/")
    response = client.post("/", json={"x": 1, "y": 2, "user": "test user"})
    assert response.status_code == 200
    assert response.json() == {"status": "success"}


def test_update_pixel_fail():
    # response = client.get("/")
    response = client.post("/", json={"x": 1, "user": "test user"})
    assert response.status_code == 400
    response = client.post("/", json={"y": 2, "user": "test user"})
    assert response.status_code == 400
    response = client.post("/", json={"x": 1, "y": 2})
    assert response.status_code == 400
    # assert response.json() == {"status": "success"}
