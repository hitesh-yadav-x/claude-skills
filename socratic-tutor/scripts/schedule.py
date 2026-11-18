"""Spaced-revision scheduling rules for the socratic tutor."""
import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

LADDER = (1, 3, 7, 16, 35)
RESULTS = ("good", "partial", "poor")
CONFIDENCE = ("guess", "fairly-sure", "sure")
SOLID_STREAK = 3


def effective_result(result, confidence):
    """Return (result, log_miss, misconception) after adjusting for confidence."""
    if result not in RESULTS:
        raise ValueError(f"bad result: {result!r}")
    if confidence not in CONFIDENCE:
        raise ValueError(f"bad confidence: {confidence!r}")
    if result == "good" and confidence == "guess":
        result = "partial"
    return result, result != "good", result == "poor" and confidence == "sure"


def _schedule(entry, today):
    entry["last_reviewed"] = today.isoformat()
    entry["next_due"] = (today + timedelta(days=LADDER[entry["step"]])).isoformat()
    return entry


def start_entry(how, today):
    if how in ("taught", "explained"):
        entry = {"status": "learning", "step": 0, "streak": 0}
    elif how == "known":
        entry = {"status": "solid", "step": 3, "streak": SOLID_STREAK}
    else:
        raise ValueError(f"bad how: {how!r}")
    entry.update(misconception=False, retired=False)
    return _schedule(entry, today)


def apply_result(entry, result, confidence, today):
    result, _, misconception = effective_result(result, confidence)
    new = dict(entry)
    if result == "good":
        new["step"] = min(new["step"] + 1, len(LADDER) - 1)
        new["streak"] += 1
        if new["streak"] >= SOLID_STREAK:
            new["status"] = "solid"
        new["misconception"] = False
    elif result == "poor":
        new["step"] = 0
        new["streak"] = 0
        new["status"] = "learning"
        new["misconception"] = new["misconception"] or misconception
    return _schedule(new, today)


def due_concepts(concepts, today):
    """Ids of non-retired concepts due on or before today, oldest first."""
    cutoff = today.isoformat()
    due = [(e["next_due"], cid) for cid, e in concepts.items()
           if not e["retired"] and e["next_due"] <= cutoff]
    return [cid for _, cid in sorted(due)]


PROGRESS = "progress.json"
SCHEMA_VERSION = 1


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{path} not found") from None
    except ValueError as e:
        raise ValueError(f"{path} is not valid JSON ({e})") from None


def load_progress(subject_dir):
    path = Path(subject_dir) / PROGRESS
    data = _read_json(path)
    if (not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION
            or not isinstance(data.get("concepts"), dict)):
        raise ValueError(f"{path} is not a valid progress file")
    return data


def save_progress(subject_dir, data):
    subject_dir = Path(subject_dir)
    tmp = subject_dir / (PROGRESS + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, subject_dir / PROGRESS)


def _source_age_days(subject_dir, today):
    path = Path(subject_dir) / "path.json"
    if not path.exists():
        return None
    source = _read_json(path).get("source")
    if not source:
        return None
    return (today - date.fromisoformat(source["fetched"])).days


def _get_entry(data, concept_id):
    if concept_id not in data["concepts"]:
        raise ValueError(f"concept {concept_id!r} has not been started; run start first")
    return data["concepts"][concept_id]


def _iso_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {text!r}") from None


def _build_parser():
    parser = argparse.ArgumentParser(prog="schedule.py")
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name, *args):
        p = sub.add_parser(name)
        p.add_argument("subject_dir")
        for a in args:
            p.add_argument(a[0], **a[1])
        p.add_argument("--today", type=_iso_date, default=None)
        return p

    command("init")
    command("start", ("concept_id", {}),
            ("how", {"choices": ["taught", "explained", "known"]}))
    rec = command("record", ("concept_id", {}), ("result", {"choices": list(RESULTS)}))
    rec.add_argument("--confidence", required=True, choices=list(CONFIDENCE))
    command("due")
    command("summary")
    command("retire", ("concept_id", {}))
    return parser


def _run(args, today):
    subject_dir = Path(args.subject_dir)
    cmd = args.command
    if cmd == "init":
        path = subject_dir / PROGRESS
        if path.exists():
            return {"created": False}
        subject_dir.mkdir(parents=True, exist_ok=True)
        save_progress(subject_dir, {"schema_version": SCHEMA_VERSION, "concepts": {}})
        return {"created": True}

    data = load_progress(subject_dir)
    concepts = data["concepts"]
    if cmd == "start":
        if args.concept_id in concepts:
            raise ValueError(f"concept {args.concept_id!r} is already started")
        concepts[args.concept_id] = start_entry(args.how, today)
        save_progress(subject_dir, data)
        return concepts[args.concept_id]
    if cmd == "record":
        entry = _get_entry(data, args.concept_id)
        if entry["retired"]:
            raise ValueError(f"concept {args.concept_id!r} is retired")
        eff, log_miss, _ = effective_result(args.result, args.confidence)
        concepts[args.concept_id] = apply_result(entry, args.result, args.confidence, today)
        save_progress(subject_dir, data)
        return dict(concepts[args.concept_id], effective_result=eff, log_miss=log_miss)
    if cmd == "retire":
        entry = _get_entry(data, args.concept_id)
        entry["retired"] = True
        save_progress(subject_dir, data)
        return entry
    if cmd == "due":
        return {"today": today.isoformat(),
                "due": due_concepts(concepts, today),
                "misconceptions": [c for c, e in concepts.items()
                                   if e["misconception"] and not e["retired"]],
                "source_age_days": _source_age_days(subject_dir, today)}
    # summary
    counts = {"new": 0, "learning": 0, "solid": 0, "retired": 0}
    for e in concepts.values():
        counts["retired" if e["retired"] else e["status"]] += 1
    counts["due"] = len(due_concepts(concepts, today))
    return counts


def main(argv=None):
    args = _build_parser().parse_args(argv)
    today = args.today or date.today()
    try:
        result = _run(args, today)
    except (ValueError, FileNotFoundError, OSError) as e:
        print(str(e).replace("\n", " "), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
