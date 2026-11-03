import json
from unittest.mock import Mock

from pet.fox_personality import choose_personality, idle_action
from utils.settings_store import SettingsStore, validate_pet


def test_random_once_and_known_value_does_not_consume_rng():
    rng = Mock()
    rng.choice.return_value = 'calm'
    assert choose_personality(None, rng) == 'calm'
    assert choose_personality('active', rng) == 'active'
    assert choose_personality([], rng) == 'calm'
    assert rng.choice.call_count == 2


def test_characters_choose_obviously_different_idle_actions():
    assert idle_action('active', .5) == 'walk'
    assert idle_action('calm', .5) == 'lie'
    assert idle_action('curious', .5) == 'idle'


def test_legacy_choice_survives_reload_and_language_save():
    class Backend:
        def __init__(self):
            self.values = {'pets': json.dumps([{'type': 'fox', 'name': 'Mia', 'position': [2, 3]}])}

        def read(self):
            return self.values

        def write(self, values):
            self.values.update(values)

    backend = Backend()
    first = SettingsStore(backend)
    first.load()
    chosen = first.roster()
    first.save(lang='en')
    second = SettingsStore(backend)
    second.load()
    assert second.roster() == chosen
    assert chosen[0]['name'] == 'Mia' and chosen[0]['position'] == [2, 3]
    assert second.lang == 'en'
    assert validate_pet({'type': 'panda', 'personality_id': 'active'}) == {'type': 'panda'}


def test_head_timeline_finishes_and_cancels_without_a_tail_clock():
    from pet.fox_reaction import FoxReaction
    reaction = FoxReaction()
    reaction.start()
    for dt, head in ((.132, 1), (.132, 2), (.792, 1), (.132, 0)):
        reaction.advance(dt)
        assert reaction.head == head
    assert not reaction.active
    reaction.start()
    reaction.cancel()
    assert reaction.head == 0 and not reaction.active


def test_valid_load_does_not_write_and_bad_json_is_not_overwritten():
    class Backend:
        def __init__(self, raw):
            self.raw = raw
            self.writes = 0

        def read(self):
            return {'pets': self.raw}

        def write(self, values):
            self.writes += 1

    for raw in ('{', json.dumps([{'type': 'fox', 'personality_id': 'calm'}])):
        backend = Backend(raw)
        SettingsStore(backend).load()
        assert backend.writes == 0


if __name__ == '__main__':
    test_random_once_and_known_value_does_not_consume_rng()
    test_characters_choose_obviously_different_idle_actions()
    test_legacy_choice_survives_reload_and_language_save()
    test_head_timeline_finishes_and_cancels_without_a_tail_clock()
    test_valid_load_does_not_write_and_bad_json_is_not_overwritten()
    print('PASS: personality selection, distinct decisions, persistent migration, head timeline')
