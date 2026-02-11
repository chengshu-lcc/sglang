# Copyright (c) Alibaba. All rights reserved.

from lmdeploy.serve.ft.metrics import kmonitor, AccMetrics
import pynvml
from threading import Lock
import time
import logging


def get_default_max_concurrency():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # 假设你有一张显卡
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    default_num = info.total // 1024 // 1024 // 1024
    pynvml.nvmlShutdown()
    logging.info(f"set default max concurrency to {default_num + 1}")
    return default_num + 1

class ConcurrencyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ConcurrencyController():
    def __init__(self, max_concurrency: int = 1, block: bool = False) -> None:
        self.max_concurrency = max_concurrency
        self.block = block

        self.lock = Lock()
        self.current_concurrency: int = 0

    def get_available_concurrency(self) -> int:
        with self.lock:
            return self.max_concurrency - self.current_concurrency

    def increment(self) -> None:
        kmonitor.report(AccMetrics.QPS_METRIC, 1)
        while(True):
            with self.lock:
                if self.current_concurrency < self.max_concurrency:
                    self.current_concurrency += 1
                    break
                else:
                    if self.block is False:
                        raise ConcurrencyException(f"Concurrency limit {self.max_concurrency} reached")
                    else:
                        time.sleep(1)

    def decrement(self) -> None:
        with self.lock:
            self.current_concurrency -= 1

    def __enter__(self) -> None:
        self.increment()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.decrement()
