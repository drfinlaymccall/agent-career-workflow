"""Regression cases found during independent release review; synthetic only."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

from careerflow import storage, templates, validation, workflow
from scripts.export_repo import export


class ReviewRegressions(unittest.TestCase):
    def test_export_never_deletes_another_writers_destination(self):
        with tempfile.TemporaryDirectory(prefix='careerflow-export-race-') as temporary:
            root = Path(temporary).resolve() / 'repo'
            (root / 'careerflow').mkdir(parents=True)
            for name in ('README.md', 'LICENSE', 'pyproject.toml', 'careerflow/__main__.py'):
                (root / name).write_text('synthetic', encoding='utf-8')
            destination = root.parent / 'release.zip'
            real_zip = zipfile.ZipFile
            created = False

            def racing_writer(*args, **kwargs):
                nonlocal created
                if not created:
                    destination.write_bytes(b'another writer owns this file')
                    created = True
                return real_zip(*args, **kwargs)

            with patch('scripts.export_repo.zipfile.ZipFile', side_effect=racing_writer):
                with self.assertRaises(FileExistsError):
                    export(root, destination)
            self.assertTrue(destination.is_file(), 'export must not delete another writer\'s output')
            self.assertEqual(destination.read_bytes(), b'another writer owns this file')

    def test_application_scaffolds_escape_untrusted_markdown_and_html(self):
        from datetime import datetime, timezone
        role = templates.demo_roles(datetime.now(timezone.utc))[0]
        role['title'] = '![external image](https://example.org/pixel)<img src="https://example.org/pixel">'
        evidence = templates.demo_evidence()[:1]
        evidence[0]['claim'] = role['title']
        evidence[0]['source'] = '[click](https://example.org/source)'
        for name, body in templates.application_files(role, evidence).items():
            self.assertNotIn('![external image](', body, name)
            self.assertNotIn('<img', body, name)
            self.assertNotIn('[click](https://example.org/source)', body, name)

    def test_preparation_can_resume_without_overwriting_reviewed_files(self):
        with tempfile.TemporaryDirectory(prefix='careerflow-preparation-') as temporary:
            vault = Path(temporary).resolve() / 'vault'
            workflow.init_vault(vault, demo=True)
            folder = vault / 'applications/demo-service-ops'
            original = {path.name: path.read_bytes() for path in folder.glob('*.md')}
            workflow.update_role(vault, 'demo-service-ops', {'status': 'current_candidate'})
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                workflow.prepare(vault, 'demo-service-ops')
            self.assertEqual(workflow.prepare(vault, 'demo-service-ops', resume=True), folder)
            self.assertEqual({path.name: path.read_bytes() for path in folder.glob('*.md')}, original)
            self.assertEqual(storage.read_record(vault / 'roles/demo-service-ops.md')[0]['status'], 'preparing')

    def test_resume_requires_a_complete_existing_scaffold(self):
        with tempfile.TemporaryDirectory(prefix='careerflow-resume-gate-') as temporary:
            vault = Path(temporary).resolve() / 'vault'
            workflow.init_vault(vault, demo=True)
            with self.assertRaisesRegex(ValueError, 'No existing'):
                workflow.prepare(vault, 'demo-community-ops', resume=True)
            workflow.update_role(vault, 'demo-service-ops', {'status': 'current_candidate'})
            (vault / 'applications/demo-service-ops/Review guide.md').unlink()
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                workflow.prepare(vault, 'demo-service-ops', resume=True)
            self.assertEqual(storage.read_record(vault / 'roles/demo-service-ops.md')[0]['status'], 'current_candidate')

    def test_unknown_practical_requirements_block_preparation(self):
        config = templates.DEFAULT_CONFIG
        for field in ('location', 'eligibility'):
            for unknown in ('tbc', 'unconfirmed'):
                with self.subTest(field=field, unknown=unknown):
                    role = workflow.normalise_lead({'id': 'example-role', 'title': 'Example role',
                                                    'organisation': 'Example service'}, config=config)
                    role.update(status='current_candidate', source_type='employer',
                                verification_status='verified', official_url='https://example.org/role',
                                last_verified='2030-01-01T09:00:00+00:00', location='Example district',
                                eligibility='Human-confirmed eligibility', fit_decision='approved',
                                evidence_ids=['example-evidence'])
                    role[field] = unknown
                    evidence = {'example-evidence': {'status': 'human_confirmed', 'synthetic': False}}
                    errors = validation.validate_role(role, config=config, evidence=evidence)
                    self.assertTrue(any(f'known {field}' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
