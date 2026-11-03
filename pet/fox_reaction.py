"""Head-only petting timeline; the existing idle clock keeps its own phase."""


class FoxReaction:
    def __init__(self):
        self.elapsed = None

    @property
    def active(self):
        return self.elapsed is not None

    def start(self):
        if not self.active:
            self.elapsed = 0.0

    def cancel(self):
        self.elapsed = None

    def advance(self, dt):
        if self.active:
            self.elapsed += max(0.0, dt)
            if self.elapsed >= 1.188:
                self.cancel()

    @property
    def head(self):
        age = self.elapsed
        if age is None or age < .132:
            return 0
        return 1 if age < .264 or age >= 1.056 else 2
