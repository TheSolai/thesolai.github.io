#!/usr/bin/env python3
"""
test_claw_doctor.py — controlled test of the doctor's log-reading logic.

Why this exists
---------------
The doctor is a point-in-time sampler of a live log. A doctor that reads the
log correctly still has to *classify* correctly, and the classification is
where the real bugs have been:

  * The first version reported 17 provider-refused overflows as a live FAIL.
    Every one of them predated the precheck fix. The verdict described
    history, not the current regime.
  * The truncation check once recommended raising `keepRecentTokens` toward
    20000 — already the value, and the loss continued at it.

Both were found by reading the log, not by testing the code. A check that has
only ever run against a real log is a check whose wrong answers look like
findings. This harness feeds the doctor synthetic events with known answers
and asserts the verdicts, so the classification is proven rather than
assumed.

What it does NOT do
-------------------
It does not touch the live log, the config, the session store, or the git
tree. It builds event lists in memory and calls the check functions directly.
The doctor stays read-only; so does this.

Usage:
    python3 scripts/health/test_claw_doctor.py
    python3 scripts/health/test_claw_doctor.py -v

Exit codes:
    0  every case matched its expected verdict
    1  a case disagreed, or the harness itself could not run
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DOCTOR_PATH = os.path.join(HERE, "claw-doctor.py")

VERBOSE = "-v" in sys.argv or "--verbose" in sys.argv


def load_doctor():
    """Import claw-doctor.py, whose filename is not a valid module name."""
    spec = importlib.util.spec_from_file_location("claw_doctor", DOCTOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {DOCTOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doc = load_doctor()

# A fixed base time keeps the synthetic events stable. The doctor's checks
# only compare timestamps against each other and against "now", and every
# event below is recent enough to fall inside any sane window.
BASE = datetime.now(timezone.utc) - timedelta(hours=2)


def minutes_ago(n):
    return BASE - timedelta(minutes=n)


def event(kind, at, text):
    """Build one event in the shape the doctor expects."""
    return {"kind": kind, "at": at, "text": text}


def overflow(at, error="400:"):
    return event(
        "overflow", at,
        f"context-overflow-diag sessionKey=agent:main:telegram:direct:1234 "
        f"error={error} compactionTokens=188093 providerPayloadBytes=813232",
    )


def precheck(at, route="compact_only"):
    return event(
        "precheck", at,
        "context-overflow-midturn-precheck sessionKey=agent:main:telegram:direct:1234 "
        "provider=minimax/MiniMax-M2.7 route=compact_only "
        "estimatedPromptTokens=188093 promptBudgetBeforeReserve=184800 "
        "overflowTokens=3293 effectiveReserveTokens=20000",
    )


def truncation(at, loss="summary-tail"):
    return event(
        "truncation", at,
        f"Compaction safeguard: finalized artifact truncated; loss={loss}",
    )


def knob_change(at, key="keepRecentTokens"):
    return event(
        "config-reload", at,
        f"config hot reload applied (agents.defaults.compaction.{key})",
    )


class OverflowAxis(unittest.TestCase):
    """The provider-refused / locally-caught axis, judged against the current regime."""

    def test_no_overflows_is_pass(self):
        check = doc.check_overflow([], 24)
        self.assertEqual(check.status, "PASS")
        self.assertIn("0 overflows", check.detail)

    def test_local_catch_only_is_pass(self):
        """The precheck working is not a failure. It is the fix working."""
        check = doc.check_overflow([overflow(minutes_ago(10), "Context")], 24)
        self.assertEqual(check.status, "PASS")
        self.assertIn("caught locally", check.detail)

    def test_refusal_after_catch_is_fail(self):
        """A provider refusal NEWER than the last local catch is a live fault."""
        events = [
            overflow(minutes_ago(30), "Context"),
            overflow(minutes_ago(20)),          # the refusal, later
        ]
        check = doc.check_overflow(events, 24)
        self.assertEqual(check.status, "FAIL")
        self.assertIn("REFUSED", check.detail + " ".join(check.evidence))

    def test_refusal_before_catch_is_not_fail(self):
        """
        The regression the first version of the doctor had: refusals that
        predate the guard are history. Reporting them as a live failure
        trains the reader to ignore the tool.
        """
        events = [
            overflow(minutes_ago(40)),          # the refusal, older
            overflow(minutes_ago(30), "Context"),
        ]
        check = doc.check_overflow(events, 24)
        self.assertEqual(check.status, "PASS")
        self.assertIn("0 provider refusals since", check.detail)

    def test_unclassified_overflow_is_warn(self):
        """An overflow with no error= field cannot be judged, so it is flagged."""
        events = [event("overflow", minutes_ago(15),
                        "context-overflow-diag sessionKey=agent:main:telegram:direct:1234")]
        check = doc.check_overflow(events, 24)
        self.assertEqual(check.status, "WARN")
        self.assertIn("unclassified", check.detail)


class PrecheckCoverageAxis(unittest.TestCase):
    """The precheck must fire as often as it catches, or it is not covering the path."""

    def test_no_overflows_is_pass(self):
        check = doc.check_precheck_coverage([], 24)
        self.assertEqual(check.status, "PASS")

    def test_matched_counts_are_pass(self):
        events = [overflow(minutes_ago(10), "Context"), precheck(minutes_ago(11))]
        check = doc.check_precheck_coverage(events, 24)
        self.assertEqual(check.status, "PASS")

    def test_precheck_without_a_catch_is_fail(self):
        """
        The precheck fired but nothing was caught. The guard is firing on a
        path that is not the one failing.
        """
        events = [precheck(minutes_ago(10))]
        check = doc.check_precheck_coverage(events, 24)
        self.assertEqual(check.status, "FAIL")
        self.assertIn("not closing the path", check.detail)

    def test_more_catches_than_prechecks_is_warn(self):
        events = [
            overflow(minutes_ago(10), "Context"),
            overflow(minutes_ago(9), "Context"),
            precheck(minutes_ago(11)),
        ]
        check = doc.check_precheck_coverage(events, 24)
        self.assertEqual(check.status, "WARN")
        self.assertIn("local catch(es) but only", check.detail)


class TruncationAxis(unittest.TestCase):
    """
    Lossy compaction, judged against the last compaction config change.

    The loss axis is a SEPARATE axis from overflow and the overflow knobs do
    not fix it. What matters here is that the boundary is honoured: a
    truncation from before the current configuration is history.
    """

    def test_no_truncations_is_pass(self):
        check = doc.check_truncation([], 24)
        self.assertEqual(check.status, "PASS")

    def test_truncation_after_knob_change_is_warn(self):
        events = [
            knob_change(minutes_ago(60)),
            truncation(minutes_ago(10)),
        ]
        check = doc.check_truncation(events, 24)
        self.assertEqual(check.status, "WARN")
        self.assertIn("lossy compaction", check.detail)

    def test_truncation_before_knob_change_is_pass(self):
        events = [
            truncation(minutes_ago(60)),
            knob_change(minutes_ago(30)),
        ]
        check = doc.check_truncation(events, 24)
        self.assertEqual(check.status, "PASS")
        self.assertIn("historical, not current", check.detail)

    def test_loss_kinds_are_counted(self):
        events = [
            knob_change(minutes_ago(60)),
            truncation(minutes_ago(20), "summary-tail,suffix-head"),
            truncation(minutes_ago(10), "summary-tail"),
        ]
        check = doc.check_truncation(events, 24)
        self.assertEqual(check.status, "WARN")
        kinds = " ".join(check.evidence)
        self.assertIn("summary-tail=2", kinds)
        self.assertIn("suffix-head=1", kinds)

    def test_the_fix_does_not_recommend_the_knob(self):
        """
        The doctor once recommended raising keepRecentTokens toward 20000 —
        already the value. The log proved the loss continued at it, in both
        directions. The recommendation must name the real mechanism.
        """
        events = [knob_change(minutes_ago(60)), truncation(minutes_ago(10))]
        check = doc.check_truncation(events, 24)
        fix = (check.fix or "").lower()
        self.assertIn("not the fix", fix)
        self.assertIn("budget", fix)


class FloodGuards(unittest.TestCase):
    """
    The 2026-10-29 flood guard.

    On 2026-10-29 at 21:17 the Claw Doctor cron announced one report of
    228,829 characters across 2,563 lines. Telegram split it into 59
    messages. The cause was `check_git_state()` counting every Rust
    build artifact as uncommitted dirt, and no cap anywhere between the
    check and the chat.

    The caps were added in the same session, but nothing TESTED them, so a
    later audit reading a stale copy concluded the caps were absent and
    that the flood was live. A guard that is not asserted is not a guard.
    These tests are the assertion.
    """

    def test_evidence_is_capped(self):
        check = doc.Check("x", "t", "WARN", "d",
                          evidence=[f"line {i}" for i in range(500)])
        self.assertLessEqual(len(check.evidence), doc.Check.MAX_EVIDENCE + 1)
        self.assertIn("more line(s)", check.evidence[-1])

    def test_detail_is_capped(self):
        """The detail string is rendered inline, so it must be bounded too.

        Capping only the evidence list leaves one enormous `detail` free to
        flood on its own — which is the shape of the original bug.
        """
        check = doc.Check("x", "t", "WARN", "D" * 200000)
        self.assertLessEqual(len(check.detail), doc.Check.MAX_DETAIL + 40)
        self.assertLess(len(check.detail), 1000)

    def test_fix_is_capped(self):
        check = doc.Check("x", "t", "WARN", "d", fix="F" * 100000)
        self.assertLessEqual(len(check.fix), doc.Check.MAX_FIX + 40)

    def test_evidence_lines_are_bounded(self):
        check = doc.Check("x", "t", "WARN", "d", evidence=["E" * 50000])
        self.assertLess(len(check.evidence[0]), 500)

    def test_cap_message_bounds_the_report(self):
        # The truncation notice is appended, so the result is slightly LONGER
        # than the cap itself. What matters is that it is bounded.
        self.assertLessEqual(len(doc.cap_message("x" * 100000)),
                             doc.MAX_MESSAGE_CHARS + 100)

    def test_cap_message_keeps_short_reports_intact(self):
        text = "a short report"
        self.assertEqual(doc.cap_message(text), text)

    def test_render_text_is_bounded(self):
        """The full (non-cron) report must also fit one message."""
        checks = [doc.Check(f"c{i}", f"title {i}", "WARN",
                            "detail " * 500,
                            evidence=[f"ev {j} " * 200 for j in range(50)])
                  for i in range(40)]
        rendered = doc.render_text(checks, 24, "test")
        self.assertLessEqual(len(rendered), doc.MAX_MESSAGE_CHARS)

    def test_render_finding_is_bounded(self):
        check = doc.Check("x", "t", "FAIL", "D" * 200000,
                          evidence=["E" * 5000 for _ in range(100)],
                          fix="F" * 50000)
        rendered = doc.render_finding(check, 24)
        self.assertLess(len(rendered), 5000)


class GitNoiseFilter(unittest.TestCase):
    """Build output is not work in progress, and must not be reported as dirt."""

    NOISE = ("/target/", "node_modules/", "/.venv/", "__pycache__/",
             "/dist/", "/build/", ".pytest_cache/")

    def test_noise_filter_constants_match_the_doctor(self):
        """The doctor's noise list must be exactly what this test expects.

        The list lives in one place (NOISE_PATTERNS) so the check and the
        test cannot drift apart silently — that drift is how a flood filter
        stops filtering.
        """
        self.assertEqual(tuple(doc.NOISE_PATTERNS), self.NOISE)

    def test_noise_paths_are_recognised(self):
        for path in ("D  projects/vellum-rs/target/debug/.fingerprint/x",
                     "?? node_modules/foo/bar.js",
                     " M app/.venv/lib/py3/x.py",
                     "?? src/__pycache__/x.pyc",
                     "?? web/dist/bundle.js",
                     "?? web/build/out.js",
                     "?? app/.pytest_cache/v/cache"):
            self.assertTrue(any(n in path for n in self.NOISE), path)

    def test_real_dirt_is_not_filtered(self):
        for path in (" M scripts/health/claw-doctor.py",
                     "?? README.md",
                     " M projects/drosscash"):
            self.assertFalse(any(n in path for n in self.NOISE), path)


class BoundaryDetection(unittest.TestCase):
    """The boundary itself must be found, and only from real knob changes."""

    def test_boundary_is_the_last_knob_change(self):
        events = [
            knob_change(minutes_ago(60)),
            knob_change(minutes_ago(30), "recentTurnsPreserve"),
            truncation(minutes_ago(40)),
        ]
        boundary = doc.last_knob_change(events)
        self.assertIsNotNone(boundary)
        self.assertEqual(boundary, minutes_ago(30))

    def test_unrelated_config_change_is_not_a_boundary(self):
        """A config change to something else is not a compaction knob change."""
        events = [event("config-reload", minutes_ago(30),
                        "config hot reload applied (agents.defaults.compaction.qualityGuard)")]
        self.assertIsNone(doc.last_knob_change(events))


def main():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    if VERBOSE:
        suite = loader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2 if VERBOSE else 1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
