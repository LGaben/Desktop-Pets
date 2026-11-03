import math
import unittest

from pet.ball import Ball
from utils.throw_gesture import ThrowGesture


class ThrowGestureTests(unittest.TestCase):
    def test_recent_momentum_not_full_drag_length(self):
        gesture = ThrowGesture()
        gesture.add(0, 0, 0)
        gesture.add(10000, 0, 10)
        gesture.add(10010, -20, 10.05)
        vx, vy = gesture.release(10020, -40, 10.1)
        self.assertGreater(vx, 0)
        self.assertLess(vy, 0)
        self.assertAlmostEqual(vx, 3.2)
        self.assertAlmostEqual(vy, -6.4)

    def test_pause_before_release_has_no_old_impulse(self):
        gesture = ThrowGesture()
        gesture.add(0, 0, 0)
        gesture.add(1000, 0, .1)
        self.assertEqual(gesture.release(1000, 0, 1), (0, 0))

    def test_speed_is_capped_and_empty_history_is_safe(self):
        gesture = ThrowGesture()
        self.assertEqual(gesture.release(0, 0, 0), (0, 0))
        vx, vy = gesture.release(100000, -100000, .001)
        self.assertAlmostEqual(math.hypot(vx, vy), 18)

    def test_launch_uses_release_center_and_rejects_nonfinite(self):
        ball = Ball()
        ball.launch(-50, 80, 3, -4)
        self.assertEqual((ball.x, ball.y, ball.vx, ball.vy), (-50, 80, 3, -4))
        self.assertTrue(ball.active)
        with self.assertRaises(ValueError):
            ball.launch(math.nan, 0, 0, 0)


if __name__ == '__main__':
    unittest.main()
