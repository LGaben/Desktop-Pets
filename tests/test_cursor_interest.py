"""Shared interest scheduling is independent of Qt and desktop timing."""
import unittest

from pet.cursor_interest import CursorInterestCoordinator


class ChoiceRng:
    def __init__(self):
        self.choices = []

    def choice(self, values):
        self.choices.append(list(values))
        return values[-1]

    def uniform(self, low, high):
        return (low + high) / 2


class CursorInterestTests(unittest.TestCase):
    def setUp(self):
        self.rng = ChoiceRng()
        self.group = CursorInterestCoordinator(self.rng)
        self.pets = {'first': (0, 0), 'second': (0, 10), 'far': (1000, 1000)}

    def tick(self, time, x=None, pets=None, blocked=False):
        return self.group.tick(time, (90 + int(time * 20) if x is None else x, 0),
                               self.pets if pets is None else pets, blocked)

    def grant(self):
        for time in (0, .2, .4):
            self.assertIsNone(self.tick(time))
        self.assertEqual(self.tick(.6), 'second')

    def test_waits_for_real_motion_and_selects_random_eligible_pet(self):
        self.grant()
        self.assertEqual(self.rng.choices, [['first', 'second']])
        self.assertEqual(self.group.expires, 3.6)

    def test_many_pets_still_have_one_owner(self):
        pets = {n: (0, 0) for n in range(100)}
        for time in (0, .2, .4, .6, .8, 1.):
            owner = self.tick(time, pets=pets)
        self.assertEqual(owner, 99)
        self.assertEqual(len(self.rng.choices), 1)

    def test_interest_ends_then_group_cools_down_without_handoff(self):
        self.grant()
        for n in range(4, 19):
            self.tick(n * .2, x=100 + n % 2 * 6)
        self.assertIsNone(self.group.owner)
        self.assertGreaterEqual(self.group.cooldown_until, 8.5)
        for n in range(19, 40):
            self.assertIsNone(self.tick(n * .2, x=100 + n % 2 * 6))
        self.assertEqual(len(self.rng.choices), 1)

    def test_stationary_cursor_never_grants_interest(self):
        for n in range(40):
            self.assertIsNone(self.tick(n * .2, x=100))
        self.assertEqual(self.rng.choices, [])

    def test_motion_that_stops_during_arming_does_not_trigger_late_run(self):
        self.tick(0, x=90)
        self.tick(.2, x=100)
        for n in range(2, 20):
            self.assertIsNone(self.tick(n * .2, x=100))
        self.assertIsNone(self.group.pending_since)

    def test_losing_eligibility_releases_owner_and_starts_shared_pause(self):
        self.grant()
        self.assertIsNone(self.tick(.8, pets={'first': (0, 0)}))
        self.assertAlmostEqual(self.group.cooldown_until, 5.8)

    def test_explicit_release_for_hover_hide_remove_or_retype_is_idempotent(self):
        self.grant()
        self.group.release('second', .7)
        self.assertIsNone(self.group.owner)
        self.group.release('second', 1.)
        self.assertAlmostEqual(self.group.cooldown_until, 5.7)

    def test_releasing_other_pet_does_not_cancel_current_interest(self):
        self.grant()
        self.group.release('first', .7)
        self.assertEqual(self.group.owner, 'second')

    def test_open_menu_or_press_cancels_and_does_not_restart_while_blocked(self):
        self.grant()
        for n in range(4, 40):
            self.assertIsNone(self.tick(n * .2, x=100 + n % 2 * 6, blocked=True))
        self.assertEqual(len(self.rng.choices), 1)

    def test_no_nearby_pet_does_not_create_distant_owner(self):
        for n in range(30):
            self.assertIsNone(self.tick(n * .2, pets={'far': (1000, -500)}))

    def test_owner_leaving_outer_radius_ends_episode(self):
        self.grant()
        self.assertIsNone(self.tick(.8, x=500))
        self.assertGreater(self.group.cooldown_until, .8)

    def test_long_hidden_gap_does_not_replay_old_motion(self):
        self.tick(0)
        self.tick(.2)
        self.assertIsNone(self.tick(100, x=100))
        self.assertIsNone(self.group.pending_since)

    def test_negative_screen_coordinates_are_ordinary_candidates(self):
        pets = {'left': (-1000, -200), 'right': (500, 400)}
        for n in range(4):
            owner = self.group.tick(n * .2, (-900 + n * 5, -200), pets)
        self.assertEqual(owner, 'left')


if __name__ == '__main__':
    unittest.main()
