import time
from typing import Callable


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
