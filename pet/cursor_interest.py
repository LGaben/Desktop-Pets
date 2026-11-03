"""One short, shared cursor-interest episode for a group of pets; no Qt."""
import math
import random


class CursorInterestCoordinator:
    def __init__(self, rng=random):
        self.rng = rng
        self.owner = None
        self.expires = 0.
        self.cooldown_until = 0.
        self.pending_since = None
        self.previous = None
        self.sampled_at = None
        self.last_motion = None

    def release(self, key, now):
        if self.owner is not None and self.owner == key:
            self.owner = None
            self.expires = 0.
            self.cooldown_until = now + self.rng.uniform(4., 6.)
            self.pending_since = None

    def tick(self, now, cursor, eligible, blocked=False):
        """eligible maps live pet identities to their screen-space centers."""
        previous, sampled = self.previous, self.sampled_at
        self.previous, self.sampled_at = cursor, now
        fresh = sampled is not None and 0 <= now - sampled <= .6
        moved = fresh and previous is not None and math.dist(cursor, previous) >= 3
        if moved:
            self.last_motion = now
        if self.owner is not None:
            center = eligible.get(self.owner)
            if blocked or not fresh or center is None or now >= self.expires or math.dist(cursor, center) > 215:
                self.release(self.owner, now)
        if blocked or not fresh:
            self.pending_since = None
            return self.owner
        if self.owner is not None or now < self.cooldown_until:
            return self.owner
        nearby = [key for key, center in eligible.items() if math.dist(cursor, center) <= 160]
        if not nearby or self.last_motion is None or now - self.last_motion > .3:
            self.pending_since = None
            return None
        if self.pending_since is None:
            if moved:
                self.pending_since = now
            return None
        if moved and now - self.pending_since >= .4 - 1e-9:
            self.owner = self.rng.choice(nearby)
            self.expires = now + self.rng.uniform(2., 4.)
            self.pending_since = None
        return self.owner
