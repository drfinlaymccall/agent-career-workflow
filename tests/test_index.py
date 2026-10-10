"""Disposable local-index checks using a wholly synthetic temporary vault."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest
from unittest.mock import patch

from careerflow.index import build_index, search


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="careerflow-index-test-")
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name) / "vault"
        self.vault.mkdir()
        (self.vault / ".private-vault").write_text("private\n", encoding="utf-8")
        self.write("profile/Role preferences.md", "# Preferences\nService operations and accessible communities.\n")
        self.write("roles/example-role.md", '---\nid: "example-role"\nkind: "role"\n---\n# Example role\nService operations in Example City.\n')
        self.write("applications/example-role/evidence-matrix.md", "# Evidence\nA 100% literal match_under_score.\n")
        self.write("output/old-digest.md", "secret-output-token")
        self.write("secrets/passwords.md", "secret-password-token")
        self.write(".git/config.md", "secret-git-token")
        self.write("arbitrary/unapproved.md", "secret-unapproved-token")
        self.write("profile/.hidden.md", "secret-hidden-token")
        self.write("profile/secrets/notes.md", "secret-nested-token")
        self.write("profile/.env", "secret-env-token")

    def write(self, relative, text):
        target = self.vault / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_build_returns_real_count_and_search_uses_relative_paths(self):
        self.assertEqual(build_index(self.vault), 3)
        results = search(self.vault, "operations")
        self.assertEqual(len(results), 2)
        self.assertEqual([entry["path"] for entry in results], sorted(entry["path"] for entry in results))
        for result in results:
            self.assertFalse(Path(result["path"]).is_absolute())
            self.assertIn("operations", result["snippet"].lower())
            self.assertLessEqual(len(result["snippet"]), 360)
        self.assertEqual(search(self.vault, "secret-"), [])

    def test_rebuild_replaces_projection_without_touching_canonical_records(self):
        path = self.vault / "roles/example-role.md"
        before = path.read_bytes()
        build_index(self.vault)
        self.assertEqual(path.read_bytes(), before)
        self.write("roles/example-role.md", "# Replaced\nA different opportunity.\n")
        (self.vault / "profile/Role preferences.md").unlink()
        self.assertEqual(build_index(self.vault), 2)
        self.assertEqual(search(self.vault, "operations"), [])
        self.assertEqual(len(search(self.vault, "different opportunity")), 1)
        self.assertEqual(sorted(p.name for p in (self.vault / "output").iterdir()), ["old-digest.md", "search.sqlite3"])

    def test_query_is_literal_and_parameterised(self):
        build_index(self.vault)
        for query in ("' OR 1=1 --", '" OR *', "missing%", "missing_", "\\"):
            self.assertEqual(search(self.vault, query), [])
        self.assertEqual(len(search(self.vault, "100%")), 1)
        self.assertEqual(len(search(self.vault, "match_under_score")), 1)
        self.assertEqual(len(search(self.vault, "operations", limit=1)), 1)
        self.assertEqual(search(self.vault, "   "), [])
        for limit in (0, -1, 101, True, "2"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                search(self.vault, "operations", limit=limit)
        with self.assertRaises(ValueError):
            search(self.vault, "x" * 4097)

    def test_index_has_private_permissions(self):
        build_index(self.vault)
        self.assertEqual(stat.S_IMODE((self.vault / "output/search.sqlite3").stat().st_mode), 0o600)
        with closing(sqlite3.connect(self.vault / "output/search.sqlite3")) as database:
            self.assertEqual(database.execute("select count(*) from documents").fetchone()[0], 3)

    def test_missing_index_is_an_explicit_error(self):
        with self.assertRaisesRegex(ValueError, "[Ii]ndex|[Rr]ebuild"):
            search(self.vault, "operations")

    @unittest.skipUnless(hasattr(os, "symlink"), "Symlinks unavailable")
    def test_symlinked_record_does_not_enter_index_or_replace_previous(self):
        build_index(self.vault)
        previous = (self.vault / "output/search.sqlite3").read_bytes()
        external = Path(self.temp.name) / "outside.md"
        external.write_text("not-vault-content", encoding="utf-8")
        (self.vault / "roles/linked.md").symlink_to(external)
        with self.assertRaises(ValueError):
            build_index(self.vault)
        self.assertEqual((self.vault / "output/search.sqlite3").read_bytes(), previous)
        self.assertEqual(search(self.vault, "not-vault-content"), [])

    @unittest.skipUnless(hasattr(os, "symlink"), "Symlinks unavailable")
    def test_symlinked_output_database_root_and_directory_are_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.vault / "roles/linkdir").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            build_index(self.vault)
        (self.vault / "roles/linkdir").unlink()
        (self.vault / "output/old-digest.md").unlink()
        (self.vault / "output").rmdir()
        (self.vault / "output").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            build_index(self.vault)
        (self.vault / "output").unlink()
        (self.vault / "output").mkdir()
        target = outside / "database.sqlite3"
        target.write_bytes(b"do not change")
        (self.vault / "output/search.sqlite3").symlink_to(target)
        with self.assertRaises(ValueError):
            build_index(self.vault)
        with self.assertRaises(ValueError):
            search(self.vault, "anything")
        alias = Path(self.temp.name) / "vault-alias"
        alias.symlink_to(self.vault, target_is_directory=True)
        with self.assertRaises(ValueError):
            build_index(alias)
        self.assertEqual(target.read_bytes(), b"do not change")

    def test_traversal_and_oversized_documents_are_rejected(self):
        with self.assertRaises(ValueError):
            build_index(self.vault / "roles" / "..")
        from careerflow.index import MAX_DOCUMENT_BYTES
        self.write("roles/large.md", "x" * (MAX_DOCUMENT_BYTES + 1))
        with self.assertRaises(ValueError):
            build_index(self.vault)
        self.assertFalse((self.vault / "output/search.sqlite3").exists())

    def test_failed_atomic_publication_preserves_the_previous_projection(self):
        build_index(self.vault)
        previous = (self.vault / "output/search.sqlite3").read_bytes()
        self.write("roles/another.md", "A new searchable record.\n")
        with patch("careerflow.index.os.replace", side_effect=OSError("Synthetic failure")):
            with self.assertRaises(OSError):
                build_index(self.vault)
        self.assertEqual((self.vault / "output/search.sqlite3").read_bytes(), previous)
        self.assertEqual(search(self.vault, "new searchable"), [])
        self.assertEqual(sorted(path.name for path in (self.vault / "output").iterdir()),
                         ["old-digest.md", "search.sqlite3"])

    def test_unicode_search_is_casefolded_and_corrupt_cache_is_explicit(self):
        self.write("profile/Example.md", "An example STRASSE with a Straße spelling.\n")
        build_index(self.vault)
        self.assertEqual(len(search(self.vault, "strasse")), 1)
        self.assertEqual(len(search(self.vault, "straße")), 1)
        (self.vault / "output/search.sqlite3").write_bytes(b"not a database")
        with self.assertRaisesRegex(ValueError, "[Rr]ebuild"):
            search(self.vault, "example")
        self.assertEqual(build_index(self.vault), 4)

    def test_non_utf8_and_nonregular_markdown_are_refused(self):
        path = self.write("roles/binary.md", "placeholder")
        path.write_bytes(b"invalid UTF-8 \xff")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            build_index(self.vault)
        path.write_bytes(b"NUL \x00 byte")
        with self.assertRaisesRegex(ValueError, "NUL"):
            build_index(self.vault)
        path.unlink()
        if hasattr(os, "mkfifo"):
            os.mkfifo(path)
            with self.assertRaisesRegex(ValueError, "regular"):
                build_index(self.vault)


if __name__ == "__main__":
    unittest.main()
