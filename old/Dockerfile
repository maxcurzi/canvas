# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
FROM ubuntu:22.04

RUN apt update
RUN apt install git -y
RUN apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev libjpeg-dev python3-setuptools python3-dev python3-numpy build-essential python3-pip python-is-python3 -y

RUN git clone https://github.com/pygame/pygame.git
WORKDIR /pygame
RUN python setup.py -config -auto
RUN python setup.py install --user

WORKDIR /
RUN mkdir app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY fastapiserver.py fastapiserver.py
COPY player.py player.py
COPY game_player.py game_player.py
COPY utils.py utils.py
COPY server.py server.py
COPY wsserver.py wsserver.py
COPY main.py main.py
COPY dbmanager.py dbmanager.py
COPY games/ games/
