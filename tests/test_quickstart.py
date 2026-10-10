"""Exercise the documented first-run path, not a remembered equivalent."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from careerflow import workflow

ROOT = Path(__file__).resolve().parents[1]


class QuickStartTests(unittest.TestCase):
    def test_repository_containment_is_rejected_without_writes(self):
        target = ROOT / ('blocked-vault-' + uuid4().hex)
        self.assertFalse(target.exists())
        for demo in (False, True):
            with self.assertRaisesRegex(ValueError, 'outside the toolkit'):
                workflow.init_vault(target, demo=demo)
            self.assertFalse(target.exists())

    def test_readme_quick_start_executes_as_written(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        block = re.search(r'```sh\n(python3 -m careerflow init.*?)```', readme, re.S)
        assert block is not None, 'README quick-start block is missing'
        with tempfile.TemporaryDirectory(prefix='careerflow-quickstart-') as directory:
            home = Path(directory).resolve()
            environment = dict(os.environ, HOME=str(home))
            # Use the suite's interpreter without changing the documented arguments.
            command = block.group(1).replace('python3 -m', f'"{sys.executable}" -m')
            result = subprocess.run(['/bin/sh', '-eu', '-c', command], cwd=ROOT, env=environment,
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('roles=8 evidence=3 feedback=3', result.stdout)
            self.assertIn('Indexed 25 local documents', result.stdout)
            self.assertTrue((home / 'career-demo/output/dashboard.html').is_file())
            self.assertTrue((home / 'career-demo/output/digest.md').is_file())

    def test_documentation_local_links_resolve(self):
        checked = 0
        for source in [ROOT / 'README.md', *sorted((ROOT / 'docs').glob('*.md')),
                       *sorted((ROOT / 'prompts').glob('*.md'))]:
            for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
                if urlsplit(target).scheme or target.startswith('#'):
                    continue
                destination = (source.parent / unquote(target.split('#', 1)[0])).resolve()
                self.assertTrue(destination.is_relative_to(ROOT), (source.name, target))
                self.assertTrue(destination.is_file(), (source.name, target))
                checked += 1
        self.assertGreater(checked, 30)


if __name__ == '__main__':
    unittest.main()
