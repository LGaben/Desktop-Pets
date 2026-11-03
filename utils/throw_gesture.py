"""Recent pointer momentum, in the ball model's pixels per 16ms tick."""
from collections import deque
import math


class ThrowGesture:
    def __init__(self):
        self.samples = deque()

    def add(self, x, y, time):
        self.samples.append((x, y, time))
        while len(self.samples) > 1 and self.samples[0][2] < time - .12:
            self.samples.popleft()

    def release(self, x, y, time):
        self.add(x, y, time)
        if len(self.samples) < 2:
            return 0.0, 0.0
        sx, sy, started = self.samples[0]
        elapsed = time - started
        if elapsed <= 0:
            return 0.0, 0.0
        vx, vy = (x - sx) / elapsed * .016, (y - sy) / elapsed * .016
        speed = math.hypot(vx, vy)
        scale = min(1.0, 18 / speed) if speed else 1.0
        return vx * scale, vy * scale
