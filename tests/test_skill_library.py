import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('skill_library', Path(__file__).resolve().parents[1] / 'scripts/skill_library.py')
assert spec is not None and spec.loader is not None
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(self, name='example', directory='source'):
        path = self.root / directory
        path.mkdir(parents=True, exist_ok=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Example\n---\nBody\n')
        return path

    def test_inventory_includes_asset_hashes_not_secrets(self):
        path = self.skill()
        (path / '.env').write_text('DO_NOT_READ')
        (path / 'script.py').write_text('print(1)')
        record = library.discover(path)[0]
        self.assertEqual(record['name'], 'example')
        self.assertEqual(set(record['files']), {'SKILL.md', 'script.py'})

    def test_symlink_and_cycle_discovery(self):
        self.skill(directory='skills/category/example')
        (self.root / 'skills/cycle').symlink_to(self.root / 'skills')
        (self.root / 'skills/broken').symlink_to(self.root / 'absent')
        self.assertEqual(len(library.discover(self.root / 'skills')), 1)

    def test_install_is_idempotent(self):
        source = self.skill()
        destination = self.root / 'destination'
        records = library.discover(source)
        plan = library.plan_install(records, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(len(library.apply_plan(plan)), 1)
        self.assertEqual((destination / 'example').resolve(), source.resolve())
        self.assertEqual(library.plan_install(records, destination)[0]['action'], 'already-installed')

    def test_conflict_prevents_entire_batch(self):
        self.skill('first', 'sources/first')
        self.skill('second', 'sources/second')
        destination = self.root / 'destination'
        (destination / 'second').mkdir(parents=True)
        plan = library.plan_install(library.discover(self.root / 'sources'), destination)
        with self.assertRaises(ValueError):
            library.apply_plan(plan)
        self.assertFalse((destination / 'first').exists())

    def test_broken_destination_is_conflict(self):
        source = self.skill()
        destination = self.root / 'destination'
        destination.mkdir()
        (destination / 'example').symlink_to(self.root / 'absent')
        self.assertEqual(library.plan_install(library.discover(source), destination)[0]['action'], 'conflict')

    def test_duplicate_name_rejected(self):
        self.skill('same', 'sources/one')
        self.skill('same', 'sources/two')
        with self.assertRaises(ValueError):
            library.plan_install(library.discover(self.root / 'sources'), self.root / 'dest')

    def test_unsafe_name_rejected(self):
        source = self.skill('../escape')
        with self.assertRaises(ValueError):
            library.plan_install(library.discover(source), self.root / 'dest')


if __name__ == '__main__':
    unittest.main()
