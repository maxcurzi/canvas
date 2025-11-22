import time
from typing import Callable
import asyncio
import logging

LOGGER = logging.getLogger(__name__)


class TimedCall:
    def __init__(self, func: Callable, interval: float = 1) -> None:
        self._interval = interval
        self._t_last = time.perf_counter()
        self._func = func

    def update(self, *args, **kwargs):
        if time.perf_counter() - self._t_last > self._interval:
            self._func(*args, **kwargs)
            self._t_last += self._interval
            return True
        return False


class PubSub:
    def __init__(self):
        self.waiter = asyncio.Future()

    def publish(self, value):
        waiter, self.waiter = self.waiter, asyncio.Future()
        try:
            waiter.set_result((value, self.waiter))
        except asyncio.exceptions.InvalidStateError as exc:
            pass  # Ignore. Most likely due to client disconnection

    async def subscribe(self):
        waiter = self.waiter
        while True:
            value, waiter = await waiter
            yield value

    __aiter__ = subscribe
