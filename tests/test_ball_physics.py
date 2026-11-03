"""Exercise the real physics independently of GUI and monitor configuration."""
import math
import unittest

from pet.ball import Ball


class Bounds:
    """Minimal bounds value: the physics needs edges, not a GUI object."""

    def __init__(self, left=-10000, top=-10000, right=10000, bottom=10000):
        self.edges = left, top, right, bottom

    def left(self):
        return self.edges[0]

    def top(self):
        return self.edges[1]

    def right(self):
        return self.edges[2]

    def bottom(self):
        return self.edges[3]


class BallPhysicsTests(unittest.TestCase):
    def test_equal_elapsed_time_gives_equal_trajectory(self):
        trajectories = []
        for interval in (0.004, 0.008, 0.016, 0.033, 0.05):
            ball = Ball()
            ball.throw(-900, -800, -875, -825)
            remaining = 0.5
            while remaining > 1e-10:
                dt = min(interval, remaining)
                ball.update(dt, Bounds())
                remaining -= dt
            trajectories.append((ball.x, ball.y, ball.vx, ball.vy))
        for trajectory in trajectories[1:]:
            for actual, expected in zip(trajectory, trajectories[0]):
                self.assertAlmostEqual(actual, expected, places=8)

    def test_free_fall_matches_constant_acceleration(self):
        ball = Ball()
        ball.throw(0, 0, 0, 0)
        for _ in range(10):
            ball.update(0.016, Bounds())
        self.assertAlmostEqual(ball.y, 0.5 * ball.gravity * 10 ** 2)
        self.assertAlmostEqual(ball.vy, ball.gravity * 10)

    def test_edges_bounce_with_negative_coordinates(self):
        bounds = Bounds(-500, -300, -1, -1)
        for x, y, vx, vy in ((-495, -100, -20, 0), (-6, -100, 20, 0),
                             (-100, -295, 0, -20), (-100, -6, 0, 20)):
            with self.subTest(position=(x, y), velocity=(vx, vy)):
                ball = Ball()
                ball.throw(x, y, x, y)
                ball.vx, ball.vy = vx, vy
                ball.update(0.008, bounds)
                self.assertGreaterEqual(ball.x, bounds.left() + ball.radius)
                self.assertLessEqual(ball.x, bounds.right() - ball.radius)
                self.assertGreaterEqual(ball.y, bounds.top() + ball.radius)
                self.assertLessEqual(ball.y, bounds.bottom() - ball.radius)
                if vx:
                    self.assertLess(ball.vx * vx, 0)
                if vy:
                    self.assertLess(ball.vy * vy, 0)

    def test_lands_and_stops_without_penetrating_floor(self):
        bounds = Bounds(0, 0, 800, 600)
        ball = Ball()
        ball.throw(400, 200, 400, 200)
        for _ in range(20000):
            ball.update(0.016, bounds)
            self.assertLessEqual(ball.y, bounds.bottom() - ball.radius)
            if not ball.active:
                break
        self.assertFalse(ball.active, "Ball should settle rather than bounce forever")
        self.assertAlmostEqual(ball.y, bounds.bottom() - ball.radius)
        self.assertEqual((ball.vx, ball.vy), (0.0, 0.0))
        stopped = dict(vars(ball))
        ball.update(0.1, bounds)
        self.assertEqual(vars(ball), stopped)

    def test_large_dt_is_capped_and_zero_negative_do_nothing(self):
        first, second = Ball(), Ball()
        for ball in (first, second):
            ball.throw(0, 0, 20, -10)
        first.update(10000, Bounds())
        second.update(0.1, Bounds())
        self.assertEqual(vars(first), vars(second))
        snapshot = dict(vars(first))
        first.update(0, Bounds())
        first.update(-10, Bounds())
        self.assertEqual(vars(first), snapshot)

    def test_inactive_ball_does_not_move(self):
        ball = Ball()
        ball.vx = ball.vy = 100
        ball.update(0.1, Bounds())
        self.assertEqual((ball.x, ball.y), (0, 0))

    def test_rethrow_resets_position_velocity_and_active_state(self):
        ball = Ball()
        ball.throw(100, 200, 200, 100)
        ball.update(0.1, Bounds())
        ball.active = False
        ball.throw(-100, -200, -80, -240)
        self.assertTrue(ball.active)
        self.assertEqual((ball.x, ball.y, ball.vx, ball.vy), (-100, -200, 4, -8))

    def test_extreme_throw_remains_finite_inside_bounds(self):
        bounds = Bounds(-500, -300, -1, -1)
        ball = Ball()
        ball.throw(-200, -200, 100000, -100000)
        for _ in range(100):
            ball.update(0.1, bounds)
            self.assertTrue(all(math.isfinite(value) for value in (ball.x, ball.y, ball.vx, ball.vy)))
            self.assertTrue(bounds.left() + ball.radius <= ball.x <= bounds.right() - ball.radius)
            self.assertTrue(bounds.top() + ball.radius <= ball.y <= bounds.bottom() - ball.radius)


if __name__ == "__main__":
    unittest.main()
