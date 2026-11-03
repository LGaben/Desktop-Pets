"""Pure keyframe/lifetime checks, runnable without Qt."""
import unittest

from ui.heart_effect import DURATION, HEART_MASK, HEIGHT, WIDTH, hearts_at


class HeartEffectTests(unittest.TestCase):
    def test_mask_is_a_small_binary_heart(self):
        self.assertEqual(len(HEART_MASK), 6)
        self.assertTrue(all(len(row) == 7 and set(row) <= {'0', '1'} for row in HEART_MASK))
        self.assertEqual(HEART_MASK[-1], '0001000')

    def test_effect_has_a_bounded_lifetime_and_three_particles(self):
        self.assertEqual(hearts_at(-1), [])
        self.assertEqual(hearts_at(DURATION), [])
        self.assertEqual(hearts_at(1000), [])
        self.assertEqual(len(hearts_at(.3)), 3)

    def test_particles_rise_and_fade(self):
        early = {x: (y, alpha) for x, y, scale, alpha in hearts_at(.3)}
        late = {x: (y, alpha) for x, y, scale, alpha in hearts_at(.7)}
        for x in early:
            self.assertLess(late[x][0], early[x][0])
            self.assertLess(late[x][1], early[x][1])

    def test_keyframes_stay_inside_the_overlay(self):
        for tick in range(96):
            for x, y, scale, alpha in hearts_at(tick / 100):
                self.assertTrue(0 <= x and x + 7 * scale <= WIDTH)
                self.assertTrue(0 <= y and y + 6 * scale <= HEIGHT)
                self.assertTrue(0 <= alpha <= 255)


if __name__ == '__main__':
    unittest.main()
