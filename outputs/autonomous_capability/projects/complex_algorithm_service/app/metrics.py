from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import time
from collections.abc import Iterator


@dataclass
class Timer:
    elapsed_ms: float = 0.0


@contextmanager
def measure() -> Iterator[Timer]:
    timer = Timer()
    started = time.perf_counter()
    try:
        yield timer
    finally:
        timer.elapsed_ms = (time.perf_counter() - started) * 1000
