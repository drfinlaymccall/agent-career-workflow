"""Public ATS fixtures only: these are not live integration tests."""
import io
import http.client
import json
import unittest
from unittest.mock import patch
import urllib.error

from careerflow import connectors


SOURCE = {"adapter": "greenhouse", "board": "example-board", "organisation": "Demonstration Guild"}
GREENHOUSE = {"jobs": [{"id": 123, "title": "Example Service Lead", "location": {"name": "Example City"},
                         "absolute_url": "https://example.org/jobs/123", "content": "<p>Untrusted content</p>"}]}
LEVER = [{"id": "abc-123", "text": "Example Operations Role", "categories": {"location": "Example City"},
          "hostedUrl": "https://jobs.lever.co/example-board/abc-123", "workplaceType": "hybrid"}]


class Response(io.BytesIO):
    def __init__(self, payload, url=None, status=200):
        super().__init__(payload)
        self.url = url
        self.status = status
        self.headers = {}

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status


class Opener:
    def __init__(self, payload, *, status=200, redirected=False):
        self.payload = payload
        self.status = status
        self.redirected = redirected
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        return Response(self.payload, "https://other.example/" if self.redirected else request.full_url, self.status)


class ConnectorTests(unittest.TestCase):
    def fetch(self, payload, source=None, **kwargs):
        opener = Opener(json.dumps(payload).encode())
        with patch("careerflow.connectors.urllib.request.build_opener", return_value=opener):
            result = connectors.fetch_source(source or SOURCE, **kwargs)
        return result, opener

    def test_greenhouse_normalises_to_unverified_leads(self):
        records, opener = self.fetch(GREENHOUSE)
        self.assertEqual(len(records), 1)
        item = records[0]
        self.assertEqual(item["id"], "greenhouse-example-board-123")
        self.assertEqual(item["status"], "lead")
        self.assertEqual(item["verification_status"], "unverified")
        self.assertEqual(item["source_type"], "official_ats")
        self.assertEqual(item["eligibility"], "unknown")
        self.assertIsNone(item["last_verified"])
        self.assertIsNone(item["closing_date"])
        self.assertFalse(item["human_interest"])
        self.assertFalse(item["synthetic"])
        request, timeout = opener.calls[0]
        self.assertEqual(request.full_url, "https://boards-api.greenhouse.io/v1/boards/example-board/jobs?content=true")
        self.assertEqual(timeout, 20.0)
        self.assertNotIn("Authorization", request.headers)

    def test_lever_uses_public_endpoint_and_safe_defaults(self):
        records, opener = self.fetch(LEVER, {**SOURCE, "adapter": "lever"})
        self.assertEqual(records[0]["title"], "Example Operations Role")
        self.assertEqual(records[0]["work_mode"], "hybrid")
        self.assertEqual(opener.calls[0][0].full_url, "https://api.lever.co/v0/postings/example-board?mode=json")
        minimal, _ = self.fetch({"jobs": [{"id": 7}]})
        self.assertEqual(minimal[0]["location"], "unknown")
        self.assertEqual(minimal[0]["fit_decision"], "pending")
        self.assertIsNone(minimal[0]["official_url"])
        self.assertEqual(minimal[0]["evidence_ids"], [])

    def test_hostile_url_is_discarded_and_text_never_executed(self):
        payload = {"jobs": [{"id": 7, "title": "<script>alert(1)</script>",
                              "absolute_url": "https://user:secret@example.org/path"}]}
        records, _ = self.fetch(payload)
        self.assertEqual(records[0]["title"], "<script>alert(1)</script>")
        self.assertIsNone(records[0]["official_url"])

    def test_source_configuration_is_bounded_before_network(self):
        with patch("careerflow.connectors.urllib.request.build_opener") as opener:
            for source in [{**SOURCE, "board": "../secret"}, {**SOURCE, "board": "x?y"},
                           {**SOURCE, "board": "https://example.org"}, {**SOURCE, "board": "x" * 500},
                           {**SOURCE, "adapter": "arbitrary"}, {**SOURCE, "organisation": None}]:
                with self.subTest(source=source), self.assertRaises(ValueError):
                    connectors.fetch_source(source)
            for timeout in (0, -1, float("inf"), float("nan"), True, 120, 10 ** 1000):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    connectors.fetch_source(SOURCE, timeout=timeout)
            opener.assert_not_called()

    def test_redirects_are_refused_even_by_unusual_transports(self):
        opener = Opener(b'{"jobs":[]}', redirected=True)
        with patch("careerflow.connectors.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(ValueError):
                connectors.fetch_source(SOURCE)
        handler = connectors._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "Found", {}, "https://other.example/"))

    def test_size_status_json_and_shape_failures_are_explicit(self):
        cases = [(b"x" * (connectors.MAX_RESPONSE_BYTES + 1), 200), (b"{}", 503),
                 (b"not-json", 200), (b'{"jobs":{}}', 200), (b'{"jobs":[{"title":"No ID"}]}', 200),
                 (b'{"jobs":[{"id":true}]}', 200), (b'{"jobs":[{"id":1,"title":[]}]}', 200),
                 (b'{"jobs":[],"jobs":[]}', 200)]
        for payload, status in cases:
            with self.subTest(status=status, size=len(payload)):
                opener = Opener(payload, status=status)
                with patch("careerflow.connectors.urllib.request.build_opener", return_value=opener):
                    with self.assertRaises(ValueError):
                        connectors.fetch_source(SOURCE)
        with self.assertRaises(ValueError):
            self.fetch({"error": "not a postings array"}, {**SOURCE, "adapter": "lever"})

    def test_failures_do_not_echo_potentially_sensitive_exceptions(self):
        with patch("careerflow.connectors.urllib.request.build_opener") as factory:
            factory.return_value.open.side_effect = urllib.error.URLError("private-token-should-not-appear")
            with self.assertRaises(ValueError) as caught:
                connectors.fetch_source(SOURCE)
        self.assertNotIn("private-token", str(caught.exception))

    def test_stable_long_ids_and_ordering_deduplication(self):
        source = {**SOURCE, "adapter": "lever", "board": "b" * 70}
        records, _ = self.fetch([{**LEVER[0], "id": "a" * 150}], source)
        self.assertRegex(records[0]["id"], r"^[a-z0-9][a-z0-9-]{0,79}$")
        again, _ = self.fetch([{**LEVER[0], "id": "a" * 150}], source)
        self.assertEqual(records, again)
        records, _ = self.fetch({"jobs": [GREENHOUSE["jobs"][0], GREENHOUSE["jobs"][0]]})
        self.assertEqual(len(records), 1)
        with self.assertRaises(ValueError):
            self.fetch({"jobs": [GREENHOUSE["jobs"][0], {**GREENHOUSE["jobs"][0], "title": "Conflicting title"}]})

    def test_public_https_url_validation(self):
        self.assertEqual(connectors.safe_public_url("https://example.org/jobs?q=one&lang=en"),
                         "https://example.org/jobs?q=one&lang=en")
        for url in (None, 7, "javascript:alert(1)", "http://example.org", "https://example.org:444/",
                    "https://user@example.org/", "https://10.0.0.1/", "https://[::1]/", "https://local.internal/",
                    "https://localhost/", "https://example.org\n/", "https://bad..example.org/", "https://example.org\\evil"):
            with self.subTest(url=url):
                self.assertIsNone(connectors.safe_public_url(url))

    def test_configured_board_case_and_underscores_are_not_normalised(self):
        records, opener = self.fetch(GREENHOUSE, {**SOURCE, "board": "Example_board"})
        self.assertIn("/Example_board/", opener.calls[0][0].full_url)
        self.assertRegex(records[0]["id"], r"^[a-z0-9][a-z0-9-]{0,79}$")
        other, _ = self.fetch(GREENHOUSE, {**SOURCE, "board": "example-board"})
        self.assertNotEqual(records[0]["id"], other[0]["id"])
        a, _ = self.fetch([{**LEVER[0], "id": "b-c"}], {**SOURCE, "adapter": "lever", "board": "a"})
        b, _ = self.fetch([{**LEVER[0], "id": "c"}], {**SOURCE, "adapter": "lever", "board": "a-b"})
        self.assertNotEqual(a[0]["id"], b[0]["id"])

    def test_transport_wiring_disables_proxies_and_redirects(self):
        opener = Opener(b'{"jobs":[]}')
        with patch("careerflow.connectors.urllib.request.build_opener", return_value=opener) as factory:
            self.assertEqual(connectors.fetch_source({**SOURCE, "url": "https://unapproved.example/"}), [])
        handlers = factory.call_args.args
        self.assertTrue(any(isinstance(handler, connectors._NoRedirect) for handler in handlers))
        proxies = [getattr(handler, "proxies") for handler in handlers if isinstance(handler, connectors.urllib.request.ProxyHandler)]
        self.assertEqual(proxies, [{}])
        self.assertEqual(opener.calls[0][0].host, "boards-api.greenhouse.io")
        with patch("careerflow.connectors.urllib.request.build_opener") as factory:
            for endpoint in ("http://api.lever.co/", "https://api.lever.co.evil.example/",
                             "https://" + "user@" + "api.lever.co/", "https://127.0.0.1/"):
                with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                    connectors._fetch_json(endpoint, 1)
            factory.assert_not_called()

    def test_elapsed_budget_content_encoding_and_record_limit(self):
        opener = Opener(b'{"jobs":[]}')
        with patch("careerflow.connectors.urllib.request.build_opener", return_value=opener), \
             patch("careerflow.connectors.time.monotonic", side_effect=[0.0, 21.0]):
            with self.assertRaisesRegex(ValueError, "timed out"):
                connectors.fetch_source(SOURCE)
        for headers in ({"Content-Encoding": "gzip"}, {"Content-Length": "invalid"},
                        {"Content-Length": str(connectors.MAX_RESPONSE_BYTES + 1)}):
            response = Response(b'{"jobs":[]}', "https://boards-api.greenhouse.io/v1/boards/example-board/jobs?content=true")
            response.headers = headers
            with patch("careerflow.connectors.urllib.request.build_opener") as factory:
                factory.return_value.open.return_value = response
                with self.assertRaises(ValueError):
                    connectors.fetch_source(SOURCE)
        with patch("careerflow.connectors.MAX_RECORDS", 0):
            with self.assertRaisesRegex(ValueError, "record limit"):
                self.fetch(GREENHOUSE)

    def test_nonfinite_json_and_incomplete_http_are_safe_failures(self):
        for payload in (b'{"jobs":[],"x":NaN}', b'{"jobs":[],"x":1e999}'):
            with patch("careerflow.connectors.urllib.request.build_opener", return_value=Opener(payload)):
                with self.assertRaisesRegex(ValueError, "malformed JSON"):
                    connectors.fetch_source(SOURCE)
        with patch("careerflow.connectors.urllib.request.build_opener") as factory:
            factory.return_value.open.side_effect = http.client.IncompleteRead(b"untrusted-response-body")
            with self.assertRaisesRegex(ValueError, "network request failed") as caught:
                connectors.fetch_source(SOURCE)
        self.assertNotIn("untrusted-response-body", str(caught.exception))

    def test_declared_total_cannot_hide_a_partial_response(self):
        self.assertEqual(len(self.fetch({**GREENHOUSE, "meta": {"total": 1}})[0]), 1)
        for total in (2, -1, True, "1"):
            with self.subTest(total=total), self.assertRaisesRegex(ValueError, "declared total"):
                self.fetch({**GREENHOUSE, "meta": {"total": total}})

    def test_normalised_fixtures_satisfy_the_core_role_contract(self):
        from careerflow.templates import DEFAULT_CONFIG
        from careerflow.validation import validate_role
        for source, fixture in ((SOURCE, GREENHOUSE), ({**SOURCE, "adapter": "lever"}, LEVER)):
            records, _ = self.fetch(fixture, source)
            for record in records:
                self.assertEqual(validate_role(record, config=DEFAULT_CONFIG, evidence={}), [])


if __name__ == "__main__":
    unittest.main()
