"""Real cursor-motion policy checks without Qt, screens, or user input hooks."""
import math
import unittest
from unittest.mock import Mock

from pet.cursor_reaction import CursorReaction


class CursorReactionTests(unittest.TestCase):
    def setUp(self):
        self.policy = CursorReaction()
        self.position = (100, 100)
        self.size = (40, 40)
        self.bounds = (0, 0, 760, 560)

    def sample(self, cursor, now, personality='curious', **kwargs):
        return self.policy.sample(cursor, self.position, self.size, self.bounds,
                                  now, personality, **kwargs)

    def test_only_real_nearby_motion_starts_a_reaction(self):
        self.assertIsNone(self.sample((230, 120), 0))
        for n in range(1, 100):
            self.assertIsNone(self.sample((230, 120), n * .2))
        self.assertIsNotNone(self.sample((240, 120), 20))

    def test_jitter_and_center_dead_zone_do_not_start_movement(self):
        self.sample((120, 120), 0)
        for n, point in enumerate(((125, 120), (123, 119), (124, 120))):
            self.assertIsNone(self.sample(point, (n + 1) * .2))
        self.policy.reset()
        self.sample((240, 120), 0)
        self.assertIsNone(self.sample((241, 121), .2))

    def test_curious_approaches_with_space_around_the_cursor(self):
        self.sample((230, 120), 0)
        x, y, animation = self.sample((240, 120), .2)
        self.assertGreater(x, 100)
        self.assertEqual(y, 100)
        self.assertGreaterEqual(math.dist((x + 20, y + 20), (240, 120)), 48)
        self.assertEqual(animation, 'run')

    def test_calm_runs_away(self):
        self.sample((230, 120), 0, 'calm')
        x, y, animation = self.sample((240, 120), .2, 'calm')
        self.assertLess(x, 100)
        self.assertEqual(y, 100)
        self.assertEqual(animation, 'run')

    def test_close_approach_walks_and_stops_outside_dead_zone(self):
        self.sample((180, 120), 0)
        x, _, animation = self.sample((190, 120), .2)
        self.assertEqual(animation, 'walk')
        self.assertGreater(x, 110)
        self.assertEqual(self.sample((160, 120), .6), (100, 100, 'idle'))

    def test_smoothing_preserves_space_when_the_cursor_comes_closer(self):
        self.sample((240, 120), 0)
        self.sample((250, 120), .2)
        x, y, _ = self.sample((185, 120), .7)
        self.assertGreaterEqual(math.dist((x + 20, y + 20), (185, 120)), 48)

    def test_rate_limit_keeps_the_current_target(self):
        self.sample((230, 120), 0)
        first = self.sample((240, 120), .2)
        self.assertIsNone(self.sample((250, 120), .3))
        self.assertEqual(self.policy.target, first[:2])
        self.assertIsNotNone(self.sample((255, 120), .65))

    def test_mode_is_stable_until_cursor_leaves_outer_radius(self):
        rng = Mock()
        rng.random.side_effect = [.9, .1]
        self.sample((230, 120), 0, 'active', rng=rng)
        self.sample((240, 120), .2, 'active', rng=rng)
        self.assertTrue(self.policy.flee)
        self.assertIsNotNone(self.sample((310, 120), .65, 'active', rng=rng))
        self.assertTrue(self.policy.flee)
        self.assertEqual(rng.random.call_count, 1)
        self.assertIsNone(self.sample((350, 120), 1.0, 'active', rng=rng))
        self.assertIsNotNone(self.sample((240, 120), 1.2, 'active', rng=rng))
        self.assertFalse(self.policy.flee)

    def test_far_motion_never_sends_pet_across_the_screen(self):
        self.sample((600, 400), 0)
        for n in range(1, 30):
            self.assertIsNone(self.sample((600 + n, 400), n * .2))

    def test_negative_screen_edges_are_reachable(self):
        self.position, self.bounds = (-100, -80), (-800, -500, -40, -40)
        self.sample((-150, -60), 0, 'calm')
        x, y, _ = self.sample((-160, -60), .2, 'calm')
        self.assertLessEqual(x, -40)
        self.assertGreaterEqual(x, -800)
        self.assertLessEqual(y, -40)
        self.assertGreaterEqual(y, -500)

    def test_clamped_target_inside_arrival_threshold_is_rejected(self):
        self.position, self.bounds = (9, 100), (0, 0, 760, 560)
        self.sample((120, 120), 0, 'calm')
        self.assertIsNone(self.sample((125, 120), .2, 'calm'))

    def test_reset_and_long_sampling_gaps_discard_stale_motion(self):
        self.sample((230, 120), 0)
        self.assertIsNone(self.sample((240, 120), 2))
        self.policy.reset((240, 120))
        self.assertIsNone(self.sample((250, 120), 2.2))
        self.assertIsNotNone(self.sample((255, 120), 2.4))

    def test_tiny_screen_does_not_generate_impossible_target(self):
        self.position, self.bounds = (0, 0), (0, 0, 0, 0)
        self.sample((120, 20), 0, 'calm')
        self.assertIsNone(self.sample((125, 20), .2, 'calm'))


if __name__ == '__main__':
    unittest.main()
