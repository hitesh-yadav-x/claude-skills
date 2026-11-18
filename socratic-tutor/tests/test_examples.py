import json
import pathlib
import subprocess
import sys
import unittest

SCRIPT = str(pathlib.Path(__file__).parent.parent / "scripts" / "schedule.py")


class Examples(unittest.TestCase):
    ROOT = pathlib.Path(__file__).parent.parent / "examples" / "sample-learner"

    def test_json_examples_parse_and_are_version_1(self):
        for rel in ("profile.json", "fractions/path.json", "fractions/progress.json"):
            data = json.loads((self.ROOT / rel).read_text())
            self.assertEqual(list(data)[0], "schema_version")
            self.assertEqual(data["schema_version"], 1)

    def test_every_progress_concept_is_on_the_path(self):
        path = json.loads((self.ROOT / "fractions/path.json").read_text())
        ids = {c["id"] for d in path["domains"] for c in d["concepts"]}
        prog = json.loads((self.ROOT / "fractions/progress.json").read_text())
        self.assertTrue(set(prog["concepts"]) <= ids)
        self.assertEqual(len(ids), len(
            [c for d in path["domains"] for c in d["concepts"]]))

    def test_schedule_script_reads_the_example(self):
        out = subprocess.run([sys.executable, SCRIPT, "summary", str(self.ROOT / "fractions"),
                              "--today", "2026-11-16"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)

    def test_page_builds_from_the_example_without_writing_into_it(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dst = pathlib.Path(tmp) / "fractions"
            shutil.copytree(self.ROOT / "fractions", dst)
            page = str(pathlib.Path(SCRIPT).parent / "build_page.py")
            out = subprocess.run([sys.executable, page, str(dst), "--today", "2026-11-16"],
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(out.stdout)["cards"], 2)


if __name__ == "__main__":
    unittest.main()
