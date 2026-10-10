"""Core tests: all people, organisations and records are synthetic fixtures."""
import concurrent.futures
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from careerflow import storage, templates, validation, workflow


class VaultCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="careerflow-test-")
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name).resolve() / "vault"
        workflow.init_vault(self.vault)

    def evidence(self, identifier="evidence-example"):
        value = {
            "schema_version": 1, "kind": "evidence", "id": identifier,
            "claim": "Coordinated an example community rota.",
            "source": "Fictional test statement", "status": "human_confirmed",
            "boundary": "No budget responsibility claimed.", "synthetic": False,
        }
        storage.write_record(self.vault / "evidence" / f"{identifier}.md", value, "Human notes\n")
        return value

    def role(self, identifier="example-role", status="lead"):
        value = workflow.normalise_lead({
            "id": identifier, "title": "Operations coordinator",
            "organisation": "Example Community Operations Cooperative",
            "source_type": "employer", "official_url": "https://example.org/jobs/ops",
        }, config=storage.load_config(self.vault))
        if status != "lead":
            self.evidence()
            value.update({
                "status": status, "verification_status": "verified",
                "last_verified": datetime.now(timezone.utc).isoformat(),
                "location": "Example district", "eligibility": "Operator checked requirements",
                "fit_decision": "approved", "evidence_ids": ["evidence-example"],
            })
        storage.write_record(self.vault / "roles" / f"{identifier}.md", value, "Keep **human** notes exactly.\n\n")
        return value

    def read_role(self, identifier="example-role"):
        return storage.read_record(self.vault / "roles" / f"{identifier}.md")


class StorageTests(VaultCase):
    def test_roundtrip_and_private_permissions(self):
        record = self.role()
        loaded, body = self.read_role()
        self.assertEqual(record, loaded)
        self.assertEqual(body, "Keep **human** notes exactly.\n\n")
        path = self.vault / "roles" / "example-role.md"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.vault.stat().st_mode), 0o700)
        self.assertEqual(storage.list_records(self.vault, "roles"), [record])

    def test_malformed_frontmatter_rejected(self):
        samples = [
            '---\nid: "one"\nid: "two"\n---\nbody',
            '---\nid: bare-yaml-is-not-json\n---\nbody',
            '---\nvalue: NaN\n---\nbody',
            '---\nvalue: {"a": 1, "a": 2}\n---\nbody',
            '---\nid: "one"\nbody without closing delimiter',
            '# no frontmatter\n',
        ]
        path = self.vault / "roles" / "bad.md"
        for text in samples:
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises((storage.StorageError, ValueError)):
                    storage.read_record(path)

    def test_symlink_record_and_parent_rejected(self):
        self.role()
        target = self.vault / "roles" / "example-role.md"
        link = self.vault / "roles" / "alias.md"
        link.symlink_to(target)
        with self.assertRaises(storage.StorageError):
            storage.read_record(link)
        with self.assertRaises(storage.StorageError):
            storage.write_record(link, {"id": "alias"}, "")
        link.unlink()
        parent = self.vault / "linked"
        parent.symlink_to(self.vault / "roles", target_is_directory=True)
        with self.assertRaises(storage.StorageError):
            storage.write_record(parent / "new.md", {"id": "new"}, "")
        with self.assertRaises(storage.StorageError):
            storage.read_record(parent / "example-role.md")

    def test_paths_and_sections_are_not_normalised_into_safety(self):
        self.role()
        with self.assertRaises(storage.StorageError):
            storage.read_record(self.vault / "roles" / ".." / "roles" / "example-role.md")
        with self.assertRaises(storage.StorageError):
            storage.list_records(self.vault, "../roles")
        for bad in ("Upper", "../role", "", "x" * 81, "white space"):
            with self.subTest(identifier=bad), self.assertRaises(ValueError):
                workflow.normalise_lead({"id": bad, "title": "Example", "organisation": "Example"}, config=storage.load_config(self.vault))

    def test_atomic_failure_leaves_previous_record(self):
        original = self.role()
        with mock.patch("careerflow.storage.os.replace", side_effect=OSError("fixture failure")):
            with self.assertRaises(OSError):
                storage.write_record(self.vault / "roles" / "example-role.md", {**original, "title": "Changed"}, "changed")
        self.assertEqual(self.read_role()[0], original)
        self.assertEqual([p.name for p in (self.vault / "roles").iterdir()], ["example-role.md"])


    def test_unicode_separators_roundtrip_without_splitting_metadata(self):
        role = self.role()
        role["title"] = "Operations\u2028coordinator\u2029example"
        body = "Human body\r\nwith\u2028separators\n"
        storage.write_record(self.vault / "roles" / "example-role.md", role, body)
        self.assertEqual(self.read_role(), (role, body))

    def test_lock_symlink_and_nonregular_record_rejected(self):
        target = self.vault / ".vault.lock"
        target.unlink()
        target.symlink_to(self.vault / "config.json")
        with self.assertRaises(storage.StorageError):
            self.role()
        target.unlink()
        directory = self.vault / "roles" / "directory.md"
        directory.mkdir()
        with self.assertRaises(storage.StorageError):
            storage.read_record(directory)

    def test_no_overwrite_and_json_overflow_rejected(self):
        role = self.role()
        with self.assertRaises(storage.StorageError):
            storage.write_record(self.vault / "roles" / "example-role.md", role, "changed", overwrite=False)
        with self.assertRaises(storage.StorageError):
            storage.strict_json_loads('{"value": 1e999}')


class ValidationTests(VaultCase):
    def test_empty_private_vault_is_valid(self):
        report = validation.validate_vault(self.vault)
        self.assertTrue(report.valid, report.errors)
        self.assertEqual({key: report.counts[key] for key in ("roles", "evidence", "feedback")}, {"roles": 0, "evidence": 0, "feedback": 0})
        self.assertEqual(storage.load_config(self.vault)["mode"], "private")
        for name in templates.PROFILE_FILES:
            self.assertTrue((self.vault / "profile" / name).is_file())

    def test_initialisation_refuses_overwrite(self):
        marker = (self.vault / "config.json").read_bytes()
        with self.assertRaises(ValueError):
            workflow.init_vault(self.vault, demo=True)
        self.assertEqual((self.vault / "config.json").read_bytes(), marker)

    def test_demo_is_valid_and_cannot_be_used_as_private(self):
        demo = Path(self.tmp.name) / "demo"
        workflow.init_vault(demo, demo=True)
        report = validation.validate_vault(demo)
        self.assertTrue(report.valid, report.errors)
        self.assertGreaterEqual(report.counts["roles"], 6)
        self.assertGreater(report.counts["feedback"], 0)
        self.assertTrue(all(role["synthetic"] for role in report.records["roles"]))
        statuses = {role["status"] for role in report.records["roles"]}
        self.assertTrue({"current_candidate", "preparing", "submitted", "withheld_unverified", "closed"} <= statuses)
        config = storage.load_config(demo)
        config["mode"] = "private"
        storage.atomic_write_text(demo / "config.json", json.dumps(config))
        self.assertFalse(validation.validate_vault(demo).valid)

    def test_duplicate_and_mismatched_ids_fail_with_actual_count(self):
        role = self.role()
        storage.write_record(self.vault / "roles" / "another.md", role, "")
        report = validation.validate_vault(self.vault)
        self.assertEqual(report.counts["roles"], 2)
        self.assertFalse(report.valid)
        self.assertTrue(any("duplicate" in error.lower() for error in report.errors), report.errors)
        self.assertTrue(any("filename" in error.lower() for error in report.errors), report.errors)

    def test_unknown_evidence_reference_fails(self):
        role = self.role()
        role["evidence_ids"] = ["missing-evidence"]
        storage.write_record(self.vault / "roles" / "example-role.md", role, "")
        self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_naive_timestamp_and_impossible_date_fail(self):
        role = self.role()
        role.update(last_verified="2026-01-01T10:00:00", closing_date="2026-02-30")
        storage.write_record(self.vault / "roles" / "example-role.md", role, "")
        report = validation.validate_vault(self.vault)
        self.assertFalse(report.valid)
        self.assertGreaterEqual(len(report.errors), 2)

    def test_malformed_file_still_counts(self):
        (self.vault / "roles" / "broken.md").write_text("not a record", encoding="utf-8")
        report = validation.validate_vault(self.vault)
        self.assertEqual(report.counts["roles"], 1)
        self.assertFalse(report.valid)

    def test_invalid_config_and_unsafe_entries_do_not_erase_counts(self):
        self.role()
        alias = self.vault / "roles" / "unsafe-alias.md"
        alias.symlink_to(self.vault / "roles" / "example-role.md")
        report = validation.validate_vault(self.vault)
        self.assertFalse(report.valid)
        self.assertEqual(report.counts["roles"], 2)
        alias.unlink()
        storage.atomic_write_text(self.vault / "config.json", "not JSON")
        report = validation.validate_vault(self.vault)
        self.assertFalse(report.valid)
        self.assertEqual(report.counts["roles"], 1)

    def test_scan_counters_and_source_records_are_validated(self):
        record = workflow.scan(self.vault)
        record["source_count"] = 100
        storage.write_record(self.vault / "scans" / f"{record['id']}.md", record, "")
        self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_boolean_schema_version_is_not_an_integer_version(self):
        role = self.role()
        role["schema_version"] = True
        storage.write_record(self.vault / "roles" / "example-role.md", role, "")
        self.assertFalse(validation.validate_vault(self.vault).valid)


    def test_malformed_field_types_report_errors_without_crashing(self):
        base = self.role()
        for key, bad in (("id", []), ("status", {}), ("evidence_ids", [1]), ("source_type", []), ("synthetic", 1), ("fit_decision", []), ("official_url", 123)):
            with self.subTest(key=key):
                storage.write_record(self.vault / "roles" / "example-role.md", {**base, key: bad}, "")
                self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_unsafe_urls_are_rejected(self):
        base = self.role()
        for url in ("javascript:alert(1)", "data:text/html,test", "file:///secrets", "https://user:secret@example.org/jobs", "https://localhost/jobs", "https://127.0.0.1/jobs", "https://[::1]/jobs", "https://2130706433/jobs", "https://example.org\\@127.0.0.1/", "https://example.org:8443/jobs"):
            with self.subTest(url=url):
                storage.write_record(self.vault / "roles" / "example-role.md", {**base, "official_url": url}, "")
                self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_bad_source_slug_timezone_and_config_duplicate_rejected(self):
        config = storage.load_config(self.vault)
        for patch in ({"timezone": "Not/AZone"}, {"max_verification_age_days": True}, {"sources": [{"adapter": "shell", "board": "../escape", "organisation": "Example"}]}):
            with self.subTest(patch=patch):
                storage.atomic_write_text(self.vault / "config.json", json.dumps({**config, **patch}))
                self.assertFalse(validation.validate_vault(self.vault).valid)
        storage.atomic_write_text(self.vault / "config.json", '{"mode":"private","mode":"demo"}')
        self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_outcome_requires_both_history_and_note(self):
        base = self.role()
        for patch in ({"status": "submitted"}, {"status": "outcome_known", "outcome_note": "Example outcome"}, {"status": "outcome_known", "submitted_at": "2026-01-01", "submission_note": "Human report"}):
            with self.subTest(patch=patch):
                storage.write_record(self.vault / "roles" / "example-role.md", {**base, **patch}, "")
                self.assertFalse(validation.validate_vault(self.vault).valid)


class LifecycleTests(VaultCase):
    def test_gate_rejection_is_atomic_and_preserves_body(self):
        before = self.role()
        with self.assertRaises(ValueError):
            workflow.update_role(self.vault, "example-role", {"status": "current_candidate", "fit_decision": "approved"})
        self.assertEqual(self.read_role()[0], before)
        self.assertEqual(self.read_role()[1], "Keep **human** notes exactly.\n\n")

    def test_supported_verified_candidate_prepare_and_submit(self):
        self.role(status="current_candidate")
        body = self.read_role()[1]
        path = workflow.prepare(self.vault, "example-role")
        self.assertTrue((path / "Evidence matrix.md").is_file())
        self.assertIn("No budget responsibility", (path / "Evidence matrix.md").read_text())
        self.assertEqual(self.read_role()[0]["status"], "preparing")
        self.assertEqual(self.read_role()[1], body)
        before = sorted(p.name for p in path.iterdir())
        with self.assertRaises(ValueError):
            workflow.prepare(self.vault, "example-role")
        self.assertEqual(sorted(p.name for p in path.iterdir()), before)
        with self.assertRaises(ValueError):
            workflow.submit(self.vault, "example-role", "2026-01-01", "Example report", human_confirmed=False)
        submitted = workflow.submit(self.vault, "example-role", "2026-01-01", "I report using the external employer form.", human_confirmed=True)
        self.assertEqual(submitted["status"], "submitted")
        self.assertEqual(submitted["submitted_at"], "2026-01-01")
        self.assertEqual(submitted["outcome_note"], "")
        self.assertEqual(self.read_role()[1], body)
        self.assertTrue(validation.validate_vault(self.vault).valid)

    def test_prepare_refuses_existing_folder_without_changing_role(self):
        self.role(status="current_candidate")
        path = self.vault / "applications" / "example-role"
        path.mkdir()
        (path / "human.txt").write_text("Keep me", encoding="utf-8")
        with self.assertRaises(ValueError):
            workflow.prepare(self.vault, "example-role")
        self.assertEqual(self.read_role()[0]["status"], "current_candidate")
        self.assertEqual((path / "human.txt").read_text(), "Keep me")

    def test_privileged_patch_fields_and_direct_prepare_are_prohibited(self):
        self.role()
        for patch in ({"id": "new-id"}, {"synthetic": True}, {"submitted_at": "2026-01-01"}, {"outcome_note": "Made up"}, {"status": "submitted"}, {"status": "preparing"}, {"unknown": "value"}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                workflow.update_role(self.vault, "example-role", patch)
        self.assertEqual(self.read_role()[0]["status"], "lead")

    def test_stale_or_expired_candidate_cannot_be_prepared(self):
        role = self.role(status="current_candidate")
        for patch in ({"last_verified": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}, {"last_verified": datetime.now(timezone.utc).isoformat(), "closing_date": "2020-01-01"}):
            role.update(patch)
            storage.write_record(self.vault / "roles" / "example-role.md", role, "")
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                workflow.prepare(self.vault, "example-role")

    def test_unconfirmed_evidence_does_not_support_a_candidate(self):
        self.role(status="current_candidate")
        path = self.vault / "evidence" / "evidence-example.md"
        evidence, body = storage.read_record(path)
        evidence["status"] = "unconfirmed"
        storage.write_record(path, evidence, body)
        self.assertFalse(validation.validate_vault(self.vault).valid)

    def test_submit_requires_preparing_date_and_meaningful_confirmation(self):
        self.role()
        with self.assertRaises(ValueError):
            workflow.submit(self.vault, "example-role", "2026-01-01", "Reported", human_confirmed=True)
        self.role(status="preparing")
        for date, note in (("2026-02-30", "Reported"), ("2026-01-01T00:00:00", "Reported"), ("2026-01-01", "  "), ("2999-01-01", "Reported")):
            with self.subTest(date=date, note=note), self.assertRaises(ValueError):
                workflow.submit(self.vault, "example-role", date, note, human_confirmed=True)


class FeedbackAndImportTests(VaultCase):
    def test_feedback_is_immutable_idempotent_and_does_not_mutate_role(self):
        original = self.role()
        first = workflow.add_feedback(self.vault, "example-role", "hide", "Not my preferred work pattern", event_id="feedback-one")
        again = workflow.add_feedback(self.vault, "example-role", "hide", "Not my preferred work pattern", event_id="feedback-one")
        self.assertEqual(first, again)
        self.assertEqual(len(storage.list_records(self.vault, "feedback")), 1)
        self.assertEqual(self.read_role()[0], original)
        with self.assertRaises(ValueError):
            workflow.add_feedback(self.vault, "example-role", "restore", "Changed preference", event_id="feedback-one")

    def test_concurrent_idempotent_feedback(self):
        self.role()
        def write(_):
            return workflow.add_feedback(self.vault, "example-role", "hide", "Example preference", event_id="shared-event")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(write, range(12)))
        self.assertTrue(all(value == results[0] for value in results))
        self.assertEqual(len(storage.list_records(self.vault, "feedback")), 1)

    def test_unknown_feedback_role_and_empty_hide_reason_rejected(self):
        self.role()
        for identifier, action, reason in (("missing", "note", "Example"), ("Example-role", "note", "Example"), ("example-role", "hide", " "), ("example-role", "submit", "Example")):
            with self.subTest(identifier=identifier, action=action), self.assertRaises(ValueError):
                workflow.add_feedback(self.vault, identifier, action, reason)
        self.assertEqual(storage.list_records(self.vault, "feedback"), [])

    def test_import_downgrades_privileged_payload_and_deduplicates(self):
        payload = {"id": "imported-role", "title": "Example coordinator", "organisation": "Example operations", "status": "submitted", "verification_status": "verified", "fit_decision": "approved", "submitted_at": "2026-01-01", "submission_note": "Untrusted claim", "evidence_ids": ["missing"]}
        result = workflow.import_leads(self.vault, [payload])
        self.assertEqual(result["imported"], 1)
        record, _ = self.read_role("imported-role")
        self.assertEqual(record["status"], "lead")
        self.assertEqual(record["verification_status"], "unverified")
        self.assertEqual(record["fit_decision"], "pending")
        self.assertIsNone(record["submitted_at"])
        self.assertIsNone(record["last_verified"])
        self.assertEqual(record["evidence_ids"], [])
        again = workflow.import_leads(self.vault, [{**payload, "title": "Replacement"}])
        self.assertEqual(again["skipped"], 1)
        self.assertEqual(self.read_role("imported-role")[0], record)

    def test_invalid_import_batch_is_atomic(self):
        valid = {"id": "valid-role", "title": "Example", "organisation": "Example"}
        for batch in ([valid, {**valid, "id": "../escape"}], [valid, valid], [valid, {**valid, "id": "synthetic-role", "synthetic": True, "source_type": "synthetic"}]):
            with self.subTest(batch=batch), self.assertRaises(ValueError):
                workflow.import_leads(self.vault, batch)
        self.assertEqual(storage.list_records(self.vault, "roles"), [])

    def test_import_never_regresses_submission_or_feedback(self):
        self.role(status="preparing")
        workflow.submit(self.vault, "example-role", "2026-01-01", "Human report", human_confirmed=True)
        workflow.add_feedback(self.vault, "example-role", "hide", "Example reason", event_id="keep-feedback")
        before = self.read_role()
        workflow.import_leads(self.vault, [{"id": "example-role", "title": "New title", "organisation": "Example"}])
        self.assertEqual(self.read_role(), before)
        self.assertEqual(len(storage.list_records(self.vault, "feedback")), 1)


class ScanTests(VaultCase):
    def sources(self, adapters=("greenhouse", "lever")):
        config = storage.load_config(self.vault)
        config["sources"] = [{"adapter": adapter, "board": "example-community", "organisation": "Fictional community operations", "ignored_command": "must not execute"} for adapter in adapters]
        storage.atomic_write_text(self.vault / "config.json", json.dumps(config))

    def test_no_sources_is_recorded_as_failed_without_network(self):
        fetcher = mock.Mock(side_effect=AssertionError("Network must not be called"))
        result = workflow.scan(self.vault, fetcher=fetcher)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["source_count"], 0)
        fetcher.assert_not_called()
        self.assertEqual(storage.list_records(self.vault, "scans"), [result])

    def test_all_sources_failed_is_recorded_and_error_is_safe(self):
        self.sources()
        fetcher = mock.Mock(side_effect=RuntimeError("private-token-must-not-be-logged"))
        result = workflow.scan(self.vault, fetcher=fetcher)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failed_sources"], 2)
        self.assertEqual(result["imported"], 0)
        self.assertNotIn("private-token", json.dumps(result))
        self.assertTrue(all(item["error"] for item in result["sources"]))
        self.assertEqual(storage.list_records(self.vault, "scans"), [result])

    def test_partial_scan_imports_only_leads_and_preserves_existing(self):
        self.sources()
        self.role(status="preparing")
        workflow.submit(self.vault, "example-role", "2026-01-01", "Human report", human_confirmed=True)
        workflow.add_feedback(self.vault, "example-role", "hide", "Existing preference", event_id="scan-feedback")
        before = self.read_role()
        def fetcher(source, *, timeout):
            self.assertEqual(set(source), {"adapter", "board", "organisation"})
            self.assertEqual(timeout, 20.0)
            if source["adapter"] == "lever":
                raise OSError("Fixture source failure")
            return [{"id": "new-source-role", "title": "Example coordinator", "organisation": "Example", "status": "current_candidate", "verification_status": "verified"}, {"id": "example-role", "title": "Changed title", "organisation": "Example"}]
        result = workflow.scan(self.vault, fetcher=fetcher)
        self.assertEqual(result["status"], "partial")
        self.assertEqual((result["imported"], result["skipped"], result["successful_sources"], result["failed_sources"]), (1, 1, 1, 1))
        self.assertEqual(self.read_role(), before)
        self.assertEqual(self.read_role("new-source-role")[0]["status"], "lead")
        self.assertEqual(self.read_role("new-source-role")[0]["verification_status"], "unverified")
        repeat = workflow.scan(self.vault, fetcher=fetcher)
        self.assertEqual((repeat["imported"], repeat["skipped"]), (0, 2))
        self.assertEqual(len(storage.list_records(self.vault, "feedback")), 1)
        self.assertEqual(len(storage.list_records(self.vault, "scans")), 2)
        self.assertTrue(validation.validate_vault(self.vault).valid)

    def test_empty_success_does_not_infer_closure(self):
        self.sources(("greenhouse",))
        before = self.role()
        result = workflow.scan(self.vault, fetcher=lambda source, **kwargs: [])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["fetched"], 0)
        self.assertEqual(self.read_role()[0], before)

    def test_invalid_source_batch_is_not_partially_imported(self):
        self.sources(("greenhouse",))
        result = workflow.scan(self.vault, fetcher=lambda source, **kwargs: [
            {"id": "good-role", "title": "Example", "organisation": "Example"},
            {"id": "../bad", "title": "Example", "organisation": "Example"},
        ])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(storage.list_records(self.vault, "roles"), [])


if __name__ == "__main__":
    unittest.main()
