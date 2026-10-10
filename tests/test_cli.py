"""Offline CLI acceptance tests with real subprocess and filesystem execution."""
from __future__ import annotations

import concurrent.futures
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from typing import Any
import unittest
from unittest import mock

from careerflow import cli, storage, validation, workflow


ROOT = Path(__file__).resolve().parent.parent


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="careerflow-cli-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.vault = self.base / "vault"

    def run_cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, "-m", "careerflow", *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def in_process(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(list(map(str, args)))
        return code, stdout.getvalue(), stderr.getvalue()

    def init_demo(self):
        self.run_cli("init", self.vault, "--demo")

    def json_file(self, name, payload):
        path = self.base / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_help_and_version(self):
        result = self.run_cli("--help")
        self.assertIn("import-leads", result.stdout)
        self.assertIn("no automatic submission", result.stdout)
        self.assertIn("careerflow", self.run_cli("--version").stdout)

    def test_private_init_validate_and_no_overwrite(self):
        self.run_cli("init", self.vault)
        result = self.run_cli("validate", self.vault)
        self.assertIn("roles=0 evidence=0 feedback=0", result.stdout)
        self.run_cli("init", self.vault, "--demo", expected=1)
        self.assertEqual(storage.load_config(self.vault)["mode"], "private")

    def test_demo_counts_match_canonical_records(self):
        self.init_demo()
        result = self.run_cli("validate", self.vault)
        for section in ("roles", "evidence", "feedback"):
            count = len(storage.list_records(self.vault, section))
            self.assertIn(f"{section}={count}", result.stdout)
        self.assertIn("synthetic", self.run_cli("init", self.base / "second", "--demo").stdout)

    def test_invalid_record_returns_nonzero_and_actual_count(self):
        self.run_cli("init", self.vault)
        (self.vault / "roles" / "malformed.md").write_text("---\nid: broken-json\n---\n", encoding="utf-8")
        result = self.run_cli("validate", self.vault, expected=1)
        self.assertIn("roles=1", result.stdout)
        self.assertIn("Malformed JSON", result.stderr)

    def test_unknown_vault_and_unsafe_id_are_friendly_errors(self):
        self.run_cli("validate", self.vault, expected=1)
        self.init_demo()
        self.run_cli("feedback", self.vault, "../escape", "note", "--reason", "Example", expected=1)
        self.run_cli("feedback", self.vault, "unknown-id", "note", "--reason", "Example", expected=1)

    def test_cli_import_and_patch_restrictions(self):
        self.run_cli("init", self.vault)
        lead = {"id": "example-import", "title": "Example service coordinator", "organisation": "Example community service", "status": "outcome_known", "verification_status": "verified"}
        path = self.json_file("leads.json", [lead])
        self.run_cli("import-leads", self.vault, path)
        actual, body = storage.read_record(self.vault / "roles" / "example-import.md")
        self.assertEqual((actual["status"], actual["verification_status"]), ("lead", "unverified"))
        patch = self.json_file("patch.json", {"human_interest": True, "gaps": ["Eligibility unknown"]})
        self.run_cli("update-role", self.vault, "example-import", "--patch", patch)
        updated, updated_body = storage.read_record(self.vault / "roles" / "example-import.md")
        self.assertTrue(updated["human_interest"])
        self.assertEqual(updated_body, body)
        bad = self.json_file("bad-patch.json", {"outcome_note": "Not evidenced"})
        self.run_cli("update-role", self.vault, "example-import", "--patch", bad, expected=1)
        self.assertEqual(storage.read_record(self.vault / "roles" / "example-import.md")[0], updated)

    def test_cli_duplicate_json_keys_are_rejected_before_mutation(self):
        self.run_cli("init", self.vault)
        path = self.base / "bad.json"
        path.write_text('[{"id":"one","id":"two","title":"Example","organisation":"Example"}]', encoding="utf-8")
        self.run_cli("import-leads", self.vault, path, expected=1)
        self.assertEqual(storage.list_records(self.vault, "roles"), [])

    def test_cli_prepare_submit_never_sends_and_requires_human_flag(self):
        self.init_demo()
        self.run_cli("prepare", self.vault, "demo-community-ops")
        self.run_cli("prepare", self.vault, "demo-community-ops", expected=1)
        today = datetime.now(timezone.utc).date().isoformat()
        self.run_cli("submit", self.vault, "demo-community-ops", "--date", today, "--confirmation", "Fictional human report", expected=1)
        output = self.run_cli("submit", self.vault, "demo-community-ops", "--date", today, "--confirmation", "Fictional human report", "--human-confirmed")
        self.assertIn("toolkit sent nothing", output.stdout)
        record, _ = storage.read_record(self.vault / "roles" / "demo-community-ops.md")
        self.assertEqual((record["status"], record["submitted_at"], record["outcome_note"]), ("submitted", today, ""))
        self.run_cli("validate", self.vault)

    def test_feedback_concurrent_processes_are_idempotent(self):
        self.init_demo()
        args = ("feedback", self.vault, "demo-community-ops", "hide", "--reason", "Synthetic preference", "--event-id", "cli-shared-event")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outputs = list(pool.map(lambda _: self.run_cli(*args), range(4)))
        self.assertTrue(all("cli-shared-event" in result.stdout for result in outputs))
        matches = [item for item in storage.list_records(self.vault, "feedback") if item["id"] == "cli-shared-event"]
        self.assertEqual(len(matches), 1)
        self.run_cli("feedback", self.vault, "demo-community-ops", "restore", "--event-id", "cli-shared-event", expected=1)
        record, _ = storage.read_record(self.vault / "roles" / "demo-community-ops.md")
        self.assertEqual(record["status"], "current_candidate")

    def test_no_source_scan_exits_nonzero_and_records_failure(self):
        self.run_cli("init", self.vault)
        result = self.run_cli("scan", self.vault, expected=1)
        self.assertIn("No sources configured", result.stdout)
        scans = storage.list_records(self.vault, "scans")
        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0]["status"], "failed")

    def test_all_source_failures_exit_nonzero_offline(self):
        workflow.init_vault(self.vault)
        config = storage.load_config(self.vault)
        config["sources"] = [{"adapter": "greenhouse", "board": "example", "organisation": "Example community"}]
        storage.atomic_write_text(self.vault / "config.json", json.dumps(config))
        module: Any = types.ModuleType("careerflow.connectors")
        module.fetch_source = mock.Mock(side_effect=OSError("Fixture only: no live request"))
        with mock.patch.dict(sys.modules, {"careerflow.connectors": module}):
            code, stdout, stderr = self.in_process("scan", self.vault)
        self.assertEqual(code, 1, stderr)
        self.assertIn("failed=1", stdout)
        self.assertEqual(len(storage.list_records(self.vault, "scans")), 1)

    def test_render_receives_actual_config_scan_counts_and_aware_now(self):
        workflow.init_vault(self.vault, demo=True)
        scan = workflow.scan(self.vault)
        config = storage.load_config(self.vault)
        config["timezone"] = "Europe/London"
        storage.atomic_write_text(self.vault / "config.json", json.dumps(config))
        module: Any = types.ModuleType("careerflow.render")
        module.render_dashboard = mock.Mock(return_value="<!doctype html><title>Offline fixture</title>")
        module.render_digest = mock.Mock(return_value=("# Offline fixture\n", "<title>Offline fixture</title>"))
        with mock.patch.dict(sys.modules, {"careerflow.render": module}):
            self.assertEqual(self.in_process("dashboard", self.vault)[0], 0)
            self.assertEqual(self.in_process("digest", self.vault)[0], 0)
        for function in (module.render_dashboard, module.render_digest):
            call = function.call_args
            self.assertEqual(call.kwargs["config"], config)
            self.assertEqual(call.kwargs["scan"], scan)
            self.assertIsNotNone(call.kwargs["now"].tzinfo)
            self.assertEqual(call.args[0], storage.list_records(self.vault, "roles"))
            self.assertEqual(call.args[1], storage.list_records(self.vault, "feedback"))
        for name in ("dashboard.html", "digest.md", "digest.html"):
            self.assertTrue((self.vault / "output" / name).is_file())

    def test_validation_precedes_render_and_output_symlinks_are_rejected(self):
        workflow.init_vault(self.vault)
        module: Any = types.ModuleType("careerflow.render")
        module.render_dashboard = mock.Mock(return_value="<title>Offline fixture</title>")
        broken = self.vault / "roles" / "broken.md"
        broken.write_text("invalid", encoding="utf-8")
        with mock.patch.dict(sys.modules, {"careerflow.render": module}):
            self.assertEqual(self.in_process("dashboard", self.vault)[0], 1)
            module.render_dashboard.assert_not_called()
            broken.unlink()
            target = self.vault / "output" / "dashboard.html"
            target.symlink_to(self.vault / "config.json")
            original = (self.vault / "config.json").read_bytes()
            self.assertEqual(self.in_process("dashboard", self.vault)[0], 1)
            self.assertEqual((self.vault / "config.json").read_bytes(), original)

    @unittest.skipUnless(importlib.util.find_spec("careerflow.render") is not None, "Presentation implementation not available yet")
    def test_real_render_displays_recorded_source_failure(self):
        workflow.init_vault(self.vault, demo=True)
        config = storage.load_config(self.vault)
        config["sources"] = [{"adapter": "greenhouse", "board": "example-board", "organisation": "Fictional community source"}]
        storage.atomic_write_text(self.vault / "config.json", json.dumps(config))
        scan = workflow.scan(self.vault, fetcher=mock.Mock(side_effect=OSError("Offline fixture")))
        self.assertEqual(scan["status"], "failed")
        self.run_cli("dashboard", self.vault)
        self.run_cli("digest", self.vault)
        for name in ("dashboard.html", "digest.md", "digest.html"):
            text = (self.vault / "output" / name).read_text()
            self.assertTrue("example-board" in text, f"{name} must identify the failing board")
            self.assertTrue("Source fetch or record validation failed" in text, f"{name} must include the recorded source error")

    @unittest.skipUnless(importlib.util.find_spec("careerflow.render") is not None and importlib.util.find_spec("careerflow.index") is not None, "Presentation/index implementation not available yet")
    def test_real_demo_projection_index_search_smoke(self):
        self.init_demo()
        self.run_cli("validate", self.vault)
        self.run_cli("dashboard", self.vault)
        self.run_cli("digest", self.vault)
        self.run_cli("index", self.vault)
        result = self.run_cli("search", self.vault, "fictional")
        self.assertNotIn("No local matches", result.stdout)
        self.run_cli("index", self.vault)
        for name in ("dashboard.html", "digest.md", "digest.html", "search.sqlite3"):
            self.assertGreater((self.vault / "output" / name).stat().st_size, 0)
        self.assertIn("synthetic", (self.vault / "output" / "dashboard.html").read_text().lower())
        self.assertTrue(validation.validate_vault(self.vault).valid)


if __name__ == "__main__":
    unittest.main()
