import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import build_page as bp  # noqa: E402

SCRIPT = str(pathlib.Path(__file__).parent.parent / "scripts" / "build_page.py")

CARDS = """## 2026-11-10 · adding-fractions
- The idea: Old card.
- How it shows up: Old.
- Watch for: nothing yet
- Source: none

## 2026-11-16 · adding-fractions
- The idea: Make the pieces the same size, then add the tops.
- How it shows up: Two fractions with different bottom numbers.
- Watch for: Adding the bottom numbers.
"""
MISSES = """## 2026-11-13 · adding-fractions
- Question: What is 1/2 + 1/3?
- Memory hook: Adding makes it bigger.

## 2026-11-15 · adding-fractions
- Memory hook: Same-size pieces first.
"""
T = date(2026, 11, 16)


class Parsing(unittest.TestCase):
    def test_later_card_for_same_concept_wins(self):
        card = bp.parse_cards(CARDS)["adding-fractions"]
        self.assertEqual(card["date"], "2026-11-16")
        self.assertEqual(card["idea"], "Make the pieces the same size, then add the tops.")
        self.assertEqual(card["watch_for"], "Adding the bottom numbers.")
        self.assertIsNone(card["source"])

    def test_hooks_are_collected_oldest_first(self):
        self.assertEqual(bp.parse_hooks(MISSES),
                         {"adding-fractions": ["Adding makes it bigger.", "Same-size pieces first."]})

    def test_empty_text_gives_nothing(self):
        self.assertEqual(bp.parse_cards(""), {})
        self.assertEqual(bp.parse_hooks(""), {})


class LooseFormats(unittest.TestCase):
    def test_unrecognised_heading_ends_the_block_and_never_overwrites_it(self):
        text = ("## 2026-11-16 \u00b7 a\n- The idea: A idea.\n\n"
                "### some other heading\n- The idea: stray.\n")
        self.assertEqual(bp.parse_cards(text)["a"]["idea"], "A idea.")

    def test_other_separators_in_the_heading_are_read(self):
        for sep in ("-", "\u2014", "\u2022", "\u00b7"):
            text = f"## 2026-11-16 \u00b7 a\n- The idea: A.\n\n## 2026-11-16 {sep} b\n- The idea: B.\n"
            cards = bp.parse_cards(text)
            self.assertEqual(cards["a"]["idea"], "A.", sep)
            self.assertEqual(cards["b"]["idea"], "B.", sep)

    def test_bold_labels_star_bullets_bom_and_wrapped_lines(self):
        text = ("\ufeff## 2026-11-16 \u00b7 a\r\n- **The idea:** First line\r\n  second line.\r\n"
                "* **How it shows up**: Shows.\r\n- Watch for: W.\r\n")
        card = bp.parse_cards(text)["a"]
        self.assertEqual(card["idea"], "First line second line.")
        self.assertEqual(card["shows_up"], "Shows.")
        self.assertEqual(card["watch_for"], "W.")

    def test_a_card_with_no_readable_field_is_not_a_card(self):
        self.assertEqual(bp.parse_cards("## 2026-11-16 \u00b7 a\nJust some prose.\n"), {})


class State(unittest.TestCase):
    def e(self, status, next_due):
        return {"status": status, "next_due": next_due, "retired": False}

    def test_states(self):
        self.assertEqual(bp.concept_state(None, T), "not-started")
        self.assertEqual(bp.concept_state(self.e("solid", "2026-11-16"), T), "due")
        self.assertEqual(bp.concept_state(self.e("learning", "2026-11-17"), T), "learning")
        self.assertEqual(bp.concept_state(self.e("solid", "2026-11-30"), T), "solid")


class SubjectCase(unittest.TestCase):
    def subject(self, **files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        path = {"schema_version": 1, "subject": "fractions", "title": "Fractions",
                "kind": "general", "source": None,
                "domains": [{"id": "d", "title": "Basics", "weight_percent": None, "concepts": [
                    {"id": "adding-fractions", "title": "Adding", "summary": "s", "doc_url": None, "retired": False},
                    {"id": "old-one", "title": "Old", "summary": "s", "doc_url": None, "retired": True},
                    {"id": "gone", "title": "Gone", "summary": "s", "doc_url": None, "retired": False},
                    {"id": "next-one", "title": "Next", "summary": "s", "doc_url": None, "retired": False}]}]}
        prog = {"schema_version": 1, "concepts": {
            "adding-fractions": {"status": "learning", "step": 0, "streak": 0, "misconception": False,
                                 "retired": False, "last_reviewed": "2026-11-16", "next_due": "2026-11-17"},
            "gone": {"status": "solid", "step": 3, "streak": 3, "misconception": False,
                     "retired": True, "last_reviewed": "2026-11-01", "next_due": "2026-11-17"}}}
        (d / "path.json").write_text(json.dumps(path))
        (d / "progress.json").write_text(json.dumps(prog))
        for name, text in files.items():
            (d / name.replace("_", ".")).write_text(text)
        return d


class Model(SubjectCase):
    def test_model_joins_the_files_and_drops_retired_concepts(self):
        m = bp.build_model(self.subject(cards_md=CARDS, misses_md=MISSES), T)
        concepts = m["domains"][0]["concepts"]
        self.assertEqual([c["id"] for c in concepts], ["adding-fractions", "next-one"])
        self.assertEqual(concepts[0]["state"], "learning")
        self.assertEqual(concepts[0]["next_due"], "2026-11-17")
        self.assertEqual(concepts[0]["card"]["date"], "2026-11-16")
        self.assertEqual(len(concepts[0]["hooks"]), 2)
        self.assertEqual(concepts[1]["state"], "not-started")
        self.assertIsNone(concepts[1]["card"])
        self.assertEqual(m["counts"], {"not-started": 1, "due": 0, "learning": 1, "solid": 0})
        self.assertEqual(m["today"], "2026-11-16")

    def test_missing_cards_and_misses_files_are_fine(self):
        m = bp.build_model(self.subject(), T)
        self.assertIsNone(m["domains"][0]["concepts"][0]["card"])
        self.assertEqual(m["domains"][0]["concepts"][0]["hooks"], [])


class Render(SubjectCase):
    def html(self, **files):
        return bp.render_html(bp.build_model(self.subject(**files), T))

    def test_page_contract(self):
        h = self.html(cards_md=CARDS, misses_md=MISSES)
        self.assertTrue(h.startswith("<title>Fractions</title>"))
        low = h.lower()
        for tag in ("<!doctype", "<html", "<head>", "<body", "<script"):
            self.assertNotIn(tag, low)
        self.assertIn('<meta name="claude:viewport-fit-sides" content="cover">', h)
        self.assertIn("max(16px, env(safe-area-inset-left, 0px))", h)
        self.assertIn("max(16px, env(safe-area-inset-right, 0px))", h)
        self.assertIn(':root:not([data-theme="light"])', h)
        self.assertIn(':root[data-theme="dark"]', h)
        self.assertIn("prefers-color-scheme: dark", h)
        self.assertNotIn("http", h.split("</style>")[0])
        h.encode("ascii")

    def test_title_is_cut_to_four_words(self):
        m = bp.build_model(self.subject(), T)
        m["title"] = "AWS Certified Generative AI Developer - Professional"
        self.assertTrue(bp.render_html(m).startswith("<title>AWS Certified Generative AI</title>"))

    def test_card_hooks_and_state_are_shown(self):
        h = self.html(cards_md=CARDS, misses_md=MISSES)
        self.assertIn("Make the pieces the same size, then add the tops.", h)
        self.assertNotIn("Old card.", h)
        self.assertIn("Same-size pieces first.", h)
        self.assertIn("back on 2026-11-17", h)

    def test_no_cards_message(self):
        self.assertIn("No cards yet.", self.html())
        self.assertNotIn("No cards yet.", self.html(cards_md=CARDS))

    def test_text_is_escaped_and_only_web_links_become_links(self):
        cards = ("## 2026-11-16 \u00b7 adding-fractions\n- The idea: <script>alert(1)</script> & more\n"
                 "- How it shows up: x\n- Watch for: x\n- Source: javascript:alert(1)\n")
        h = self.html(cards_md=cards)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; more", h)
        self.assertNotIn('href="javascript:', h)

    def test_web_source_becomes_a_link(self):
        cards = ("## 2026-11-16 \u00b7 adding-fractions\n- The idea: x\n- How it shows up: x\n"
                 "- Watch for: x\n- Source: https://example.com/a?b=1&c=2\n")
        self.assertIn('href="https://example.com/a?b=1&amp;c=2"', self.html(cards_md=cards))


class Cli(SubjectCase):
    def run_cli(self, d):
        return subprocess.run([sys.executable, SCRIPT, str(d), "--today", "2026-11-16"],
                              capture_output=True, text=True)

    def test_writes_page_and_reports(self):
        d = self.subject(cards_md=CARDS)
        r = self.run_cli(d)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out, {"page": str((d / "page.html").resolve()), "concepts": 2, "cards": 1})
        self.assertIn("Fractions", (d / "page.html").read_text())
        self.assertEqual(sorted(p.name for p in d.iterdir()),
                         ["cards.md", "page.html", "path.json", "progress.json"])

    def test_missing_path_json_fails_cleanly(self):
        d = self.subject()
        (d / "path.json").unlink()
        r = self.run_cli(d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("path.json not found", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse((d / "page.html").exists())

    def test_bad_path_json_fails_cleanly(self):
        d = self.subject()
        (d / "path.json").write_text("{not json")
        r = self.run_cli(d)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertFalse((d / "page.html").exists())


TABLE_CARD = """## 2026-11-16 · lens
- The idea: Six pillars.
  | Pillar | What it asks |
  |---|:---|
  | Security | Protect <endpoints> |
  | Reliability | Handle failures |
  Apply it at each stage.
- How it shows up: A review.
"""


class Tables(unittest.TestCase):
    def test_table_rows_keep_their_own_lines(self):
        idea = bp.parse_cards(TABLE_CARD)["lens"]["idea"]
        self.assertEqual(idea.splitlines(), [
            "Six pillars.", "| Pillar | What it asks |", "|---|:---|",
            "| Security | Protect <endpoints> |", "| Reliability | Handle failures |",
            "Apply it at each stage."])

    def test_field_after_a_table_is_still_read(self):
        self.assertEqual(bp.parse_cards(TABLE_CARD)["lens"]["shows_up"], "A review.")

    def test_table_is_rendered_with_text_around_it(self):
        out = bp._field_html(bp.parse_cards(TABLE_CARD)["lens"]["idea"])
        self.assertEqual(out, (
            "<p>Six pillars.</p>"
            "<table><thead><tr><th>Pillar</th><th>What it asks</th></tr></thead>"
            "<tbody><tr><td>Security</td><td>Protect &lt;endpoints&gt;</td></tr>"
            "<tr><td>Reliability</td><td>Handle failures</td></tr></tbody></table>"
            "<p>Apply it at each stage.</p>"))

    def test_table_without_a_rule_row_has_no_header(self):
        out = bp._field_html("| a | b |\n| c | d |")
        self.assertEqual(out, "<table><tbody><tr><td>a</td><td>b</td></tr>"
                              "<tr><td>c</td><td>d</td></tr></tbody></table>")

    def test_plain_field_is_unchanged(self):
        self.assertEqual(bp._field_html("A | B & more"), "A | B &amp; more")


NOTED = """## 2026-11-12 · adding-fractions
- Note: Written before the card existed.

## 2026-11-16 · adding-fractions
- The idea: Same-size pieces.
- Note: A cross-Region profile keeps
  requests inside its own geography.
- Note: Second note.

## 2026-11-16 · next-one
- Note: Only a note here.
"""


class Notes(SubjectCase):
    def test_notes_are_collected_across_entries_oldest_first(self):
        self.assertEqual(bp.parse_notes(NOTED), {
            "adding-fractions": ["Written before the card existed.",
                                 "A cross-Region profile keeps requests inside its own geography.",
                                 "Second note."],
            "next-one": ["Only a note here."]})

    def test_a_note_alone_is_not_a_card_and_leaves_card_fields_alone(self):
        cards = bp.parse_cards(NOTED)
        self.assertEqual(list(cards), ["adding-fractions"])
        self.assertEqual(cards["adding-fractions"]["idea"], "Same-size pieces.")

    def test_model_carries_notes(self):
        concepts = bp.build_model(self.subject(cards_md=NOTED), T)["domains"][0]["concepts"]
        self.assertEqual(len(concepts[0]["notes"]), 3)
        self.assertEqual(concepts[1]["notes"], ["Only a note here."])
        self.assertEqual(bp.build_model(self.subject(), T)["domains"][0]["concepts"][0]["notes"], [])

    def test_notes_are_shown_with_and_without_a_card(self):
        h = bp.render_html(bp.build_model(self.subject(cards_md=NOTED), T))
        self.assertEqual(h.count("Your notes"), 2)
        self.assertIn("Second note.", h)
        self.assertIn("Only a note here.", h)
        self.assertNotIn("Your notes", bp.render_html(bp.build_model(self.subject(cards_md=CARDS), T)))

    def test_note_text_is_escaped(self):
        cards = "## 2026-11-16 · next-one\n- Note: <b>x</b>\n"
        h = bp.render_html(bp.build_model(self.subject(cards_md=cards), T))
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", h)


if __name__ == "__main__":
    unittest.main()
