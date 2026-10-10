"""Tests for publication controls and unsent email generation."""
import tempfile
import unittest
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

from scripts.privacy_check import scan
from scripts.export_repo import export
from scripts.draft_email import make_draft


class ReleaseTests(unittest.TestCase):
    def test_scan_reserved_addresses_and_private_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / 'README.md'
            p.write_text('reader@example.org\n', encoding='utf-8')
            self.assertEqual(scan(root)[1], [])
            p.write_text('reader@' + 'real-company.com\n', encoding='utf-8')
            self.assertTrue(scan(root)[1])
            p.write_text('A synthetic sentence.', encoding='utf-8')
            self.assertTrue(scan(root, ['synthetic sentence'])[1])
            p.write_text('/' + 'home/' + 'someone/private', encoding='utf-8')
            self.assertTrue(scan(root)[1])

    def test_symlink_and_private_file_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.private-vault').write_text('private')
            self.assertTrue(scan(root)[1])
            (root / '.private-vault').unlink()
            (root / 'README.md').write_text('safe')
            (root / 'link.md').symlink_to(root / 'README.md')
            self.assertTrue(scan(root)[1])

    def test_export_is_allowlisted_and_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            root.mkdir()
            (root / 'careerflow').mkdir()
            for name in ('README.md', 'LICENSE', 'pyproject.toml', 'careerflow/__main__.py'):
                (root / name).write_text('synthetic')
            (root / 'not-part-of-release.md').write_text('not exported')
            destination = Path(tmp) / 'release.zip'
            result = export(root, destination)
            self.assertEqual(result['files'], 4)
            with zipfile.ZipFile(destination) as archive:
                self.assertEqual(len(archive.namelist()), 5)
                self.assertNotIn('agent-career-workflow/not-part-of-release.md', archive.namelist())
            with self.assertRaises(ValueError):
                export(root, destination)
            with self.assertRaises(ValueError):
                export(root, root / 'unsafe.zip')

    def test_unsent_email_and_header_injection(self):
        data = make_draft('Digest body', 'sender@example.org', 'reader@example.org', 'Career digest')
        parsed = BytesParser(policy=policy.default).parsebytes(data)
        self.assertEqual(parsed['X-Unsent'], '1')
        self.assertEqual(parsed['To'], 'reader@example.org')
        self.assertIn('Digest body', parsed.get_content())
        for bad in ('bad\nBcc: other@example.org', '', 'one@example.org,two@example.org'):
            with self.assertRaises(ValueError):
                make_draft('body', bad, 'reader@example.org', 'Subject')
        with self.assertRaises(ValueError):
            make_draft('body', 'sender@example.org', 'reader@example.org', 'Bad\nBcc: x')


if __name__ == '__main__':
    unittest.main()
