import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = str(pathlib.Path(__file__).parent.parent / "scripts" / "schedule.py")
TODAY = "2026-11-16"


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name
        self.progress = os.path.join(self.dir, "progress.json")

    def run_cli(self, *args, today=TODAY):
        argv = [sys.executable, SCRIPT, *args]
        if today:
            argv += ["--today", today]
        return subprocess.run(argv, capture_output=True, text=True)

    def ok(self, *args, today=TODAY):
        r = self.run_cli(*args, today=today)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def disk(self):
        with open(self.progress) as f:
            return json.load(f)


class Commands(CliTest):
    def test_init_creates_empty_progress_and_never_overwrites(self):
        self.assertEqual(self.ok("init", self.dir), {"created": True})
        self.assertEqual(self.disk(), {"schema_version": 1, "concepts": {}})
        self.ok("start", self.dir, "a", "taught")
        self.assertEqual(self.ok("init", self.dir), {"created": False})
        self.assertIn("a", self.disk()["concepts"])

    def test_start_then_record_round_trip(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "s3", "taught")
        out = self.ok("record", self.dir, "s3", "good", "--confidence", "sure",
                      today="2026-11-17")
        self.assertEqual(out["step"], 1)
        self.assertEqual(out["next_due"], "2026-11-20")
        self.assertEqual(out["effective_result"], "good")
        self.assertIs(out["log_miss"], False)
        stored = self.disk()["concepts"]["s3"]
        expected = {k: v for k, v in out.items()
                    if k not in ("effective_result", "log_miss")}
        self.assertEqual(stored, expected)
        self.assertNotIn("effective_result", stored)
        self.assertNotIn("log_miss", stored)

    def test_record_lucky_guess_reports_partial_and_log_miss(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught")
        out = self.ok("record", self.dir, "a", "good", "--confidence", "guess")
        self.assertEqual(out["effective_result"], "partial")
        self.assertIs(out["log_miss"], True)

    def test_due_and_summary(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught", today="2026-11-10")
        self.ok("start", self.dir, "b", "known")
        self.ok("start", self.dir, "c", "taught", today="2026-11-10")
        self.ok("retire", self.dir, "c")
        self.assertEqual(self.ok("due", self.dir), {
            "today": TODAY, "due": ["a"], "misconceptions": [],
            "source_age_days": None})
        with open(os.path.join(self.dir, "path.json"), "w") as f:
            json.dump({"schema_version": 1,
                       "source": {"url": "x", "fetched": "2026-08-01"}}, f)
        self.assertEqual(self.ok("due", self.dir)["source_age_days"], 107)
        self.assertEqual(self.ok("summary", self.dir), {
            "new": 0, "learning": 1, "solid": 1, "retired": 1, "due": 1})

    def test_due_lists_misconceptions_even_when_not_due(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught", today="2026-11-10")
        self.ok("record", self.dir, "a", "poor", "--confidence", "sure")
        out = self.ok("due", self.dir)
        self.assertIn("a", out["misconceptions"])
        self.assertNotIn("a", out["due"])

    def test_due_returns_oldest_first(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught", today="2026-11-10")
        self.ok("start", self.dir, "b", "taught", today="2026-11-01")
        self.assertEqual(self.ok("due", self.dir)["due"], ["b", "a"])

    def test_no_temporary_file_left_behind(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught")
        self.ok("record", self.dir, "a", "good", "--confidence", "sure")
        self.assertEqual(os.listdir(self.dir), ["progress.json"])


class Errors(CliTest):
    def test_start_twice_is_an_error(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught")
        before = pathlib.Path(self.progress).read_bytes()
        r = self.run_cli("start", self.dir, "a", "known")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already started", r.stderr)
        self.assertEqual(pathlib.Path(self.progress).read_bytes(), before)

    def test_record_unstarted_concept_is_an_error(self):
        self.ok("init", self.dir)
        r = self.run_cli("record", self.dir, "ghost", "good", "--confidence", "sure")
        self.assertEqual(r.returncode, 1)
        self.assertIn("run start first", r.stderr)
        self.assertEqual(self.disk()["concepts"], {})

    def test_record_requires_confidence(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught")
        r = self.run_cli("record", self.dir, "a", "good")
        self.assertNotEqual(r.returncode, 0)

    def test_missing_progress_file_is_an_error(self):
        r = self.run_cli("due", self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("progress.json", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertEqual(os.listdir(self.dir), [])

    def test_corrupt_progress_file_is_an_error_and_is_left_alone(self):
        pathlib.Path(self.progress).write_text("{not json")
        r = self.run_cli("record", self.dir, "a", "good", "--confidence", "sure")
        self.assertEqual(r.returncode, 1)
        self.assertIn("progress.json", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertEqual(pathlib.Path(self.progress).read_bytes(), b"{not json")
        self.assertEqual(os.listdir(self.dir), ["progress.json"])

    def test_bad_today_is_an_error(self):
        self.ok("init", self.dir)
        r = self.run_cli("due", self.dir, today="16/11/2026")
        self.assertNotEqual(r.returncode, 0)

    def test_retired_concept_cannot_be_recorded(self):
        self.ok("init", self.dir)
        self.ok("start", self.dir, "a", "taught")
        self.ok("retire", self.dir, "a")
        r = self.run_cli("record", self.dir, "a", "good", "--confidence", "sure")
        self.assertEqual(r.returncode, 1)
        self.assertIn("retired", r.stderr)


if __name__ == "__main__":
    unittest.main()
