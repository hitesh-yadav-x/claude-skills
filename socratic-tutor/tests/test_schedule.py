import unittest
from datetime import date
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import schedule as s

D = date(2026, 11, 16)

class EffectiveResult(unittest.TestCase):
    def test_plain_results_pass_through(self):
        self.assertEqual(s.effective_result("good", "sure"), ("good", False, False))
        self.assertEqual(s.effective_result("partial", "fairly-sure"), ("partial", True, False))
        self.assertEqual(s.effective_result("poor", "guess"), ("poor", True, False))
    def test_lucky_guess_counts_as_partial_and_is_logged(self):
        self.assertEqual(s.effective_result("good", "guess"), ("partial", True, False))
    def test_confident_wrong_is_a_misconception(self):
        self.assertEqual(s.effective_result("poor", "sure"), ("poor", True, True))
    def test_rejects_unknown_values(self):
        with self.assertRaises(ValueError): s.effective_result("great", "sure")
        with self.assertRaises(ValueError): s.effective_result("good", "certain")

class StartEntry(unittest.TestCase):
    def test_taught_starts_on_first_step_due_tomorrow(self):
        self.assertEqual(s.start_entry("taught", D), {
            "status": "learning", "step": 0, "streak": 0,
            "last_reviewed": "2026-11-16", "next_due": "2026-11-17",
            "misconception": False, "retired": False})
    def test_explained_is_the_same_as_taught(self):
        self.assertEqual(s.start_entry("explained", D), s.start_entry("taught", D))
    def test_known_is_solid_and_checked_in_16_days(self):
        e = s.start_entry("known", D)
        self.assertEqual((e["status"], e["step"], e["streak"], e["next_due"]),
                         ("solid", 3, 3, "2026-12-02"))
    def test_rejects_unknown_how(self):
        with self.assertRaises(ValueError): s.start_entry("forgotten", D)

class ApplyResult(unittest.TestCase):
    def test_good_climbs_one_step(self):
        e = s.apply_result(s.start_entry("taught", D), "good", "sure", date(2026, 11, 17))
        self.assertEqual((e["step"], e["streak"], e["status"], e["next_due"], e["last_reviewed"]),
                         (1, 1, "learning", "2026-11-20", "2026-11-17"))
    def test_third_good_in_a_row_becomes_solid(self):
        e = s.start_entry("taught", D)
        for _ in range(3): e = s.apply_result(e, "good", "sure", D)
        self.assertEqual((e["status"], e["step"], e["streak"]), ("solid", 3, 3))
    def test_step_is_capped_at_35_days(self):
        e = s.start_entry("taught", D)
        for _ in range(9): e = s.apply_result(e, "good", "sure", D)
        self.assertEqual((e["step"], e["next_due"]), (4, "2026-12-21"))
    def test_partial_repeats_the_gap_and_keeps_streak(self):
        e = s.apply_result(s.start_entry("taught", D), "good", "sure", D)
        e2 = s.apply_result(e, "partial", "fairly-sure", D)
        self.assertEqual((e2["step"], e2["streak"], e2["next_due"]), (1, 1, "2026-11-19"))
    def test_poor_resets_and_demotes_solid(self):
        e = s.apply_result(s.start_entry("known", D), "poor", "fairly-sure", D)
        self.assertEqual((e["status"], e["step"], e["streak"], e["next_due"]),
                         ("learning", 0, 0, "2026-11-17"))
    def test_confident_wrong_sets_misconception_and_good_clears_it(self):
        e = s.apply_result(s.start_entry("taught", D), "poor", "sure", D)
        self.assertTrue(e["misconception"])
        self.assertFalse(s.apply_result(e, "good", "sure", D)["misconception"])
    def test_lucky_guess_does_not_climb_or_clear_misconception(self):
        e = s.apply_result(s.start_entry("taught", D), "poor", "sure", D)
        e2 = s.apply_result(e, "good", "guess", D)
        self.assertEqual((e2["step"], e2["misconception"]), (0, True))
    def test_early_review_is_scheduled_from_today(self):
        e = s.start_entry("known", D)  # due 2026-12-02
        e2 = s.apply_result(e, "good", "sure", date(2026, 11, 20))
        self.assertEqual((e2["step"], e2["next_due"]), (4, "2026-12-25"))
    def test_does_not_mutate_its_argument(self):
        e = s.start_entry("taught", D); before = dict(e)
        s.apply_result(e, "good", "sure", D)
        self.assertEqual(e, before)

class DueConcepts(unittest.TestCase):
    def test_lists_due_oldest_first_and_skips_future_and_retired(self):
        a = s.start_entry("taught", date(2026, 11, 10))   # due 11-11
        b = s.start_entry("taught", date(2026, 11, 1))    # due 11-02
        c = s.start_entry("taught", D)                    # due 11-17, not yet
        r = dict(s.start_entry("taught", date(2026, 10, 1)), retired=True)
        self.assertEqual(s.due_concepts({"a": a, "b": b, "c": c, "r": r}, D), ["b", "a"])
    def test_due_today_is_included_and_ties_sort_by_id(self):
        x = s.start_entry("taught", date(2026, 11, 15))
        self.assertEqual(s.due_concepts({"z": x, "y": dict(x)}, D), ["y", "z"])

if __name__ == "__main__":
    unittest.main()
