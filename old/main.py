from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_main():
    return {"message": "Hello world!!"}
