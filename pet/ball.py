from PyQt5.QtWidgets import QApplication  # used only inside update()

class Ball:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.radius = 5
        self.active = False
        self.gravity = 0.5
        self.damping = 0.85
        self.traction = 0.9

    def throw(self, start_x, start_y, end_x, end_y):
        self.x = start_x
        self.y = start_y
        dx = end_x - start_x
        dy = end_y - start_y
        self.vx = dx * 0.2
        self.vy = dy * 0.2
        self.active = True

    def update(self):
        if not self.active:
            return
        self.vy += self.gravity
        avail = QApplication.desktop().availableGeometry()
        floor_y = 40
        left = avail.x()
        top = avail.y()
        right = avail.right()
        bottom = avail.bottom()
        if self.y + self.radius > bottom - floor_y:
            self.y = bottom - floor_y - self.radius
            self.vy = -self.vy * self.damping
            self.vx *= self.traction
            if abs(self.vy) < 0.5:
                self.vy = 0
        if self.x - self.radius < left:
            self.x = left + self.radius
            self.vx = -self.vx * self.damping
        elif self.x + self.radius > right:
            self.x = right - self.radius
            self.vx = -self.vx * self.damping
        self.x += self.vx
        self.y += self.vy
        at_rest = (
            abs(self.vx) < 0.1 and abs(self.vy) < 0.5
            and self.y >= bottom - floor_y - self.radius - 1
        )
        if at_rest:
            self.active = False
