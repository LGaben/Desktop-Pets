"""SQLite integration checks runnable independently of Qt/pytest."""
import tempfile
import unittest
from pathlib import Path
from utils.database import PetDatabase


class StorageTests(unittest.TestCase):
    def test_independent_databases_and_achievement_uniqueness(self):
        with tempfile.TemporaryDirectory() as temp:
            first = PetDatabase(Path(temp) / "first.db")
            second = PetDatabase(Path(temp) / "second.db")
            data = dict(name="A", pet_type="fox", hunger=70, happiness=80,
                        energy=90, health=100, level=2, exp=20,
                        position_x=-100, position_y=-50, last_save="2026-01-01T00:00:00")
            first.save_pet(data)
            self.assertEqual(first.load_pet(), data)
            self.assertIsNone(second.load_pet())
            self.assertTrue(first.save_achievement("one", "First"))
            self.assertFalse(first.save_achievement("one", "Duplicate"))
            first.clear_data()
            self.assertIsNone(first.load_pet())
            self.assertEqual(first.get_achievements(), [])


if __name__ == "__main__":
    unittest.main()
