"""Small, Qt-free movement policy for a moving cursor near a pet."""
import math
import random


class CursorReaction:
    def __init__(self):
        self.reset()

    def reset(self, cursor=None):
        self.previous = cursor
        self.last_sample = None
        self.last_plan = None
        self.engaged = False
        self.flee = False
        self.target = None

    def sample(self, cursor, position, size, bounds, now, personality=None, rng=random):
        """Return a reachable (x, y, animation), or leave current activity alone.

        Bounds contain allowed window top-lefts, not screen pixel extents.
        Sampling continues while idle; callers reset the baseline while blocked.
        """
        previous, sampled = self.previous, self.last_sample
        self.previous, self.last_sample = cursor, now
        # Discard motion across pauses or delayed UI ticks.
        if previous is None or sampled is None or now - sampled > .6 or now < sampled:
            self.engaged = False
            self.target = None
            return None
        dx = cursor[0] - (position[0] + size[0] / 2)
        dy = cursor[1] - (position[1] + size[1] / 2)
        distance = math.hypot(dx, dy)
        if distance > (215 if self.engaged else 160):
            self.engaged = False
            self.target = None
            return None
        if self.engaged and (distance < 12 or (not self.flee and distance <= 48)):
            self.target = None
            return position[0], position[1], 'idle'
        if math.dist(cursor, previous) < 3 or distance < 12:
            return None
        if self.last_plan is not None and now - self.last_plan < .4:
            return None
        if not self.engaged:
            self.flee = (personality == 'calm' or
                         (personality != 'curious' and rng.random() >= .65))
            self.engaged = True
        if not self.flee and distance <= 48:
            return None
        step = 105 if self.flee else min(85, distance - 48)
        sign = -1 if self.flee else 1
        x = position[0] + sign * dx / distance * step
        y = position[1] + sign * dy / distance * step
        direct = x, y
        if self.target:
            old_dx, old_dy = self.target[0] - position[0], self.target[1] - position[1]
            if (old_dx * dx + old_dy * dy) * sign > 0:
                x, y = .3 * self.target[0] + .7 * x, .3 * self.target[1] + .7 * y
        if not self.flee and math.dist((x + size[0] / 2, y + size[1] / 2), cursor) < 48:
            x, y = direct
        left, top, right, bottom = bounds
        x, y = round(max(left, min(x, right))), round(max(top, min(y, bottom)))
        if math.dist((x, y), position) < 14:
            return None
        self.target = x, y
        self.last_plan = now
        return x, y, 'run' if self.flee or distance >= 110 else 'walk'
