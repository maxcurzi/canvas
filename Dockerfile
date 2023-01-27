# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
FROM python:3.11-alpine

COPY fastapiserver.py fastapiserver.py
COPY player.py player.py
COPY game_player.py game_player.py
COPY utils.py utils.py
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt


