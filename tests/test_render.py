"""Synthetic, offline checks for projections and untrusted presentation data."""
from copy import deepcopy
from datetime import datetime, timezone
from html.parser import HTMLParser
import base64
import hashlib
import re
import shutil
import subprocess
import unittest

from careerflow.render import render_dashboard, render_digest


NOW = datetime(2030, 5, 10, 12, tzinfo=timezone.utc)
CONFIG = {"mode": "private", "timezone": "UTC", "max_verification_age_days": 7}


def role(identifier="example-role", **changes):
    value = {
        "schema_version": 1, "kind": "role", "id": identifier,
        "title": "Service Operations Lead", "organisation": "Demonstration Guild",
        "status": "current_candidate", "official_url": "https://example.org/jobs/1",
        "source_type": "official_ats", "verification_status": "verified",
        "last_verified": "2030-05-09T12:00:00+00:00", "closing_date": None,
        "location": "Example City", "work_mode": "hybrid", "eligibility": "Confirmed for this example",
        "match_reasons": ["Relevant service experience"], "gaps": ["Scope to confirm"],
        "evidence_ids": ["example-evidence"], "fit_decision": "approved",
        "human_interest": False, "submitted_at": None, "submission_note": "",
        "outcome_note": "", "synthetic": False,
    }
    value.update(changes)
    return value


class Document(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.tags = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def counts(self):
        attrs = next(attrs for tag, attrs in self.tags if tag == "main")
        return {key.removeprefix("data-count-"): int(value)
                for key, value in attrs.items() if key.startswith("data-count-")}

    def cards(self):
        return [attrs for tag, attrs in self.tags if tag == "article" and "data-role-id" in attrs]


class RenderTests(unittest.TestCase):
    def render(self, roles, feedback=(), **kwargs):
        return render_dashboard(roles, list(feedback), config=kwargs.pop("config", CONFIG), now=NOW, **kwargs)

    def test_counts_are_a_partition_and_match_both_digests(self):
        roles = [role("fresh"), role("preparing", status="preparing"),
                 role("stale", last_verified="2030-05-01T00:00:00Z"),
                 role("expired", closing_date="2030-05-09"),
                 role("submitted", status="submitted", submitted_at="2030-05-01"),
                 role("outcome", status="outcome_known", outcome_note="Example outcome"),
                 role("lead", status="lead"), role("closed", status="closed"),
                 role("withheld", status="withheld_unverified"), role("hidden")]
        feedback = [{"id": "event-a", "role_id": "hidden", "action": "hide", "reason": "Not relevant",
                     "recorded_at": "2030-05-10T10:00:00Z"}]
        html = self.render(roles, feedback)
        expected = {"total": 10, "current": 2, "recheck": 2, "tracker": 2, "other": 3, "hidden": 1}
        self.assertEqual(Document(html).counts(), expected)
        self.assertEqual(len(Document(html).cards()), expected["total"])
        md, digest = render_digest(roles, feedback, config=CONFIG, now=NOW)
        self.assertEqual(Document(digest).counts(), expected)
        for label, key in [("Current candidates", "current"), ("Needs recheck", "recheck"),
                           ("Submission tracker", "tracker"), ("Other records", "other"), ("Hidden", "hidden")]:
            self.assertIn(f"| {label} | {expected[key]} |", md)
        self.assertEqual(sum(expected[k] for k in expected if k != "total"), expected["total"])

    def test_feedback_order_uses_timestamp_then_id_without_mutation(self):
        roles = [role()]
        events = [
            {"id": "b", "role_id": "example-role", "action": "restore", "recorded_at": "2030-05-10T10:00:00Z"},
            {"id": "a", "role_id": "example-role", "action": "hide", "recorded_at": "2030-05-10T12:00:00+02:00"},
            {"id": "old", "role_id": "example-role", "action": "hide", "recorded_at": "2030-05-01T10:00:00Z"},
        ]
        before = deepcopy((roles, events))
        self.assertEqual(Document(self.render(roles, events)).counts()["current"], 1)
        self.assertEqual((roles, events), before)
        self.assertEqual(self.render(roles, events), self.render(roles, list(reversed(events))))

    def test_synthetic_is_prominent_and_only_current_in_demo(self):
        example = role(synthetic=True, source_type="synthetic", verification_status="synthetic", last_verified=None)
        private = self.render([example])
        demo = self.render([example], config={**CONFIG, "mode": "demo"})
        self.assertEqual(Document(private).counts()["current"], 0)
        self.assertEqual(Document(demo).counts()["current"], 1)
        for html in (private, demo):
            self.assertIn("SYNTHETIC", html)
            self.assertIn("not real opportunities", html)
        self.assertNotIn("Officially verified", demo)

    def test_current_lane_rejects_unverified_future_and_unknown_eligibility(self):
        roles = [role("unverified", verification_status="unverified"),
                 role("future", last_verified="2030-05-11T00:00:00Z"),
                 role("unknown", eligibility="unknown"), role("fit", fit_decision="pending"),
                 role("source", source_type="aggregator"), role("no-evidence", evidence_ids=[])]
        self.assertEqual(Document(self.render(roles)).counts()["recheck"], len(roles))

    def test_date_only_deadline_respects_timezone_and_does_not_invent_time(self):
        now = datetime(2030, 5, 10, 0, 30, tzinfo=timezone.utc)
        html = render_dashboard([role(closing_date="2030-05-09")], [],
                                config={**CONFIG, "timezone": "America/Los_Angeles"}, now=now)
        self.assertEqual(Document(html).counts()["current"], 1)
        self.assertIn("time unknown", html)
        self.assertIn("within three calendar days", html)
        self.assertNotIn("23:59", html)
        self.assertNotIn("72 hours", html)
        edge = self.render([role(closing_date="2030-05-13")])
        self.assertIn("within three calendar days", edge)
        self.assertNotIn("within three calendar days", self.render([role(closing_date="2030-05-14")]))

    def test_all_untrusted_text_is_escaped_and_links_are_safe(self):
        hostile = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
        rows = [role("hostile", title=hostile, organisation=hostile, location=hostile,
                     match_reasons=[hostile], gaps=[hostile], outcome_note=hostile)]
        html = self.render(rows)
        parsed = Document(html)
        self.assertFalse(any(tag in {"img", "iframe", "object"} for tag, _ in parsed.tags))
        self.assertIn("&lt;img", html)
        self.assertEqual(sum(tag == "script" for tag, _ in parsed.tags), 1)
        for unsafe in ["javascript:alert(1)", "data:text/html,test", "file:///private", "http://example.org/",
                       "https://user:password@example.org/", "https://127.0.0.1/", "https://[::1]/",
                       "https://localhost/", "https://example.org\\@evil.example/", "https://example.org/\nfoo"]:
            with self.subTest(url=unsafe):
                result = Document(self.render([role(official_url=unsafe)]))
                self.assertFalse(any(attrs.get("href", "").startswith(("https:", "http:", "javascript:", "data:", "file:"))
                                     for _, attrs in result.tags))
        md, _ = render_digest(rows, [], config=CONFIG, now=NOW)
        self.assertNotIn("<img", md)
        self.assertNotIn("<script>", md)

    def test_coverage_is_honest_and_source_failure_is_visible(self):
        self.assertIn("No scan recorded", self.render([]))
        html = self.render([], scan={"recorded_at": "2030-05-10T10:00:00Z", "status": "partial",
            "sources": [{"adapter": "greenhouse", "board": "example", "status": "ok", "count": 3},
                        {"adapter": "lever", "board": "example", "status": "error", "error": "Timed out"}]})
        self.assertIn("Timed out", html)
        self.assertIn("Source failure", html)
        self.assertIn("not a labour-market census", html)
        self.assertIn("No roles in this lane", html)
        scan = {"status": "failed", "sources": [{"organisation": "Example source guild", "adapter": "lever",
                "board": "example-board", "status": "failed", "error": "Fixture failure"}]}
        for text in render_digest([], [], config=CONFIG, now=NOW, scan=scan):
            self.assertIn("Example source guild", text)
            self.assertIn("example-board", text)
            self.assertIn("Fixture failure", text)

    def test_render_is_deterministic_and_accessible(self):
        roles = [role("z", title="Z role"), role("a", title="A role")]
        self.assertEqual(self.render(roles), self.render(list(reversed(roles))))
        self.assertEqual(render_digest(roles, [], config=CONFIG, now=NOW),
                         render_digest(list(reversed(roles)), [], config=CONFIG, now=NOW))
        doc = Document(self.render(roles))
        ids = [attrs["id"] for _, attrs in doc.tags if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        controls = [attrs for tag, attrs in doc.tags if tag in {"input", "select", "textarea"}]
        labels = {attrs["for"] for tag, attrs in doc.tags if tag == "label" and "for" in attrs}
        self.assertTrue(all(attrs.get("id") in labels for attrs in controls))
        self.assertTrue(any(attrs.get("aria-live") == "polite" for _, attrs in doc.tags))
        self.assertTrue(any(attrs.get("name") == "viewport" for _, attrs in doc.tags))

    def test_feedback_controls_have_no_save_route(self):
        html = self.render([role()])
        self.assertIn("NOT SAVED", html)
        self.assertIn("clipboard", html)
        self.assertIn("Select and copy", html)
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "sendBeacon", "<form", "onclick="):
            self.assertNotIn(forbidden, html)
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
        self.assertEqual(len(scripts), 1)
        if shutil.which("node"):
            result = subprocess.run(["node", "--check"], input=scripts[0], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for tag, attrs in Document(html).tags:
            self.assertFalse(tag in {"script", "link", "img"} and any(key in attrs for key in ("src", "href")))

    def test_empty_and_invalid_snapshot_inputs(self):
        html = self.render([])
        self.assertEqual(Document(html).counts()["total"], 0)
        with self.assertRaises(ValueError):
            self.render([role(), role()])
        with self.assertRaises(ValueError):
            self.render([], config={**CONFIG, "timezone": "Not/AZone"})
        with self.assertRaises(ValueError):
            render_digest([], [], config=CONFIG, now=datetime(2030, 1, 1))

    def test_csp_hashes_authorise_only_the_static_script_and_style(self):
        markup = self.render([role()])
        policy = next(attrs["content"] for tag, attrs in Document(markup).tags
                      if tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy")
        for tag in ("style", "script"):
            match = re.search(rf"<{tag}>(.*?)</{tag}>", markup, re.S)
            assert match is not None
            block = match.group(1)
            digest = base64.b64encode(hashlib.sha256(block.encode()).digest()).decode()
            self.assertIn(f"{tag}-src 'sha256-{digest}'", policy)
        self.assertIn("connect-src 'none'", policy)
        self.assertNotIn("unsafe-inline", policy)
        self.assertNotIn("unsafe-eval", policy)

    def test_no_sources_failure_and_completion_time_are_not_hidden(self):
        scan = {"status": "failed", "sources": [], "source_count": 0,
                "started_at": "2030-05-10T10:00:00Z", "completed_at": "2030-05-10T10:01:00Z",
                "coverage_note": "No sources configured; no network calls or vacancy checks were made."}
        markup = self.render([], scan=scan)
        md, digest = render_digest([], [], config=CONFIG, scan=scan, now=NOW)
        for text in (markup, md, digest):
            self.assertIn("No sources configured", text)
            self.assertIn("10:01:00Z", text)
            self.assertNotIn("10:00:00Z", text)

    def test_freshness_boundary_is_exact_and_projection_does_not_rewrite_state(self):
        current = role(last_verified="2030-05-03T12:00:00Z")
        self.assertEqual(Document(self.render([current])).counts()["current"], 1)
        stale = role(last_verified="2030-05-03T11:59:59Z")
        markup = self.render([stale])
        self.assertEqual(Document(markup).counts()["recheck"], 1)
        self.assertEqual(stale["status"], "current_candidate")

    @unittest.skipUnless(shutil.which("node"), "Optional Node.js browserless interaction check")
    def test_feedback_and_filters_execute_without_any_save_capability(self):
        # A small DOM double executes the real script; it is not a browser test.
        match = re.search(r"<script>(.*?)</script>", self.render([role()]), re.S)
        assert match is not None
        script = match.group(1)
        runner = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const code = require('node:fs').readFileSync(0, 'utf8');
class Element {
  constructor() { this.value=''; this.textContent=''; this.dataset={}; this.hidden=false;
    this.disabled=false; this.events={}; this.attributes={}; this.focused=false; this.selected=false; }
  addEventListener(name, fn) { this.events[name] = fn; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.focused=true; }
  select() { this.selected=true; }
}
const ids={};
for (const name of ['role-search','lane-filter','filter-status','feedback-panel','feedback-role',
 'feedback-action','feedback-reason','feedback-prompt','copy-prompt','feedback-status','close-feedback']) ids[name]=new Element();
const first=new Element(); first.dataset={roleId:'example-one',lane:'current'}; first.textContent='Example service lead';
const second=new Element(); second.dataset={roleId:'example-two',lane:'hidden'}; second.textContent='Example hidden role';
const cards=[first,second];
const lanes=cards.map(card => { const el=new Element(); el.dataset.laneSection=card.dataset.lane;
 el.querySelectorAll=()=>[card]; const count=new Element(); el.querySelector=()=>count; return el; });
const buttons=cards.map(card => { const el=new Element(); el.dataset={roleId:card.dataset.roleId,
 hidden:card.dataset.lane==='hidden'?'true':'false'}; return el; });
const document={getElementById:id=>ids[id],querySelectorAll:selector=>
 selector==='article[data-role-id]'?cards:selector==='section[data-lane-section]'?lanes:buttons};
let copied=null;
const navigator={clipboard:{writeText:async text=>{copied=text;}}};
const window={isSecureContext:false};
vm.runInNewContext(code,{document,navigator,window,console});
(async()=>{
  assert.match(ids['filter-status'].textContent,/Showing 2 of 2/);
  ids['role-search'].value='does not exist'; ids['role-search'].events.input();
  assert.equal(cards.filter(card=>!card.hidden).length,0);
  ids['role-search'].value=''; ids['lane-filter'].value='current'; ids['lane-filter'].events.change();
  assert.equal(first.hidden,false); assert.equal(second.hidden,true);
  buttons[0].events.click(); assert.equal(ids['feedback-panel'].hidden,false);
  assert.equal(ids['feedback-role'].textContent,'example-one');
  ids['feedback-action'].value='hide'; ids['feedback-action'].events.change();
  assert.equal(ids['copy-prompt'].disabled,true); assert.equal(ids['feedback-reason'].required,true);
  assert.equal(ids['feedback-prompt'].value,'');
  ids['feedback-reason'].value='Example reason <script> is plain data'; ids['feedback-reason'].events.input();
  assert.equal(ids['copy-prompt'].disabled,false);
  const payload=JSON.parse(ids['feedback-prompt'].value.split('\n\n').at(-1));
  assert.equal(payload.role_id,'example-one'); assert.equal(payload.action,'hide');
  assert.equal(payload.reason,'Example reason <script> is plain data');
  await ids['copy-prompt'].events.click();
  assert.equal(ids['feedback-prompt'].selected,true); assert.equal(copied,null);
  assert.match(ids['feedback-status'].textContent,/NOT SAVED/);
  window.isSecureContext=true; await ids['copy-prompt'].events.click();
  assert.equal(copied,ids['feedback-prompt'].value);
  assert.match(ids['feedback-status'].textContent,/COPIED, NOT SAVED/);
  assert.equal(first.dataset.lane,'current');
  ids['close-feedback'].events.click(); assert.equal(ids['feedback-panel'].hidden,true);
  assert.equal(buttons[0].focused,true);
  buttons[1].events.click(); assert.equal(ids['feedback-action'].value,'restore');
  console.log('BROWSERLESS_INTERACTIONS_OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
        result = subprocess.run(["node", "-e", runner], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BROWSERLESS_INTERACTIONS_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
