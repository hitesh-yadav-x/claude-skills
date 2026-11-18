"""Build one HTML page for a subject from its path, progress, cards and misses."""
import argparse
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[\u00b7\u2022|:\-\u2013\u2014]\s*(\S+)\s*$")
ANY_HEADING = re.compile(r"^#{1,6}\s")
FIELD = re.compile(r"^\s*[-*]\s+\**([^:*]+?)\**\s*:\**\s*(.*)$")
CARD_FIELDS = {"The idea": "idea", "How it shows up": "shows_up",
               "Watch for": "watch_for", "Source": "source"}
STATES = ("not-started", "due", "learning", "solid")


def _blocks(text):
    """Yield (date, concept_id, [[label, text], ...]) for each '## date · id' block.

    Any other heading ends the block before it, so its lines are never read
    into the wrong concept. A line that is not a field continues the field above it.
    A table row (a line starting with '|') keeps its own line, and so does the
    line after one, so a field can hold a table with text before and after it.
    """
    current, last = None, None
    for line in text.lstrip("\ufeff").splitlines():
        m = HEADING.match(line)
        if m or ANY_HEADING.match(line):
            if current:
                yield current
            current = (m.group(1), m.group(2), []) if m else None
            last = None
            continue
        if not current:
            continue
        f = FIELD.match(line)
        if f:
            last = [f.group(1).strip(), f.group(2).strip()]
            current[2].append(last)
        elif line.strip() and last:
            so_far, more = last[1], line.strip()
            in_table = more.startswith("|") or so_far.rsplit("\n", 1)[-1].startswith("|")
            last[1] = (so_far + ("\n" if in_table else " ") + more).strip()
        else:
            last = None
    if current:
        yield current


def parse_cards(text):
    """Concept id -> card. A later card for the same concept replaces an earlier one.

    A block with none of the three card fields is not a card, so the page falls
    back to the concept's summary instead of showing an empty box.
    """
    cards = {}
    for day, cid, items in _blocks(text):
        fields = dict(items)
        card = {"date": day}
        for label, key in CARD_FIELDS.items():
            card[key] = fields.get(label) or None
        if card["idea"] or card["shows_up"] or card["watch_for"]:
            cards[cid] = card
    return cards


def parse_hooks(text):
    """Concept id -> its memory hooks from the miss log, oldest first."""
    hooks = {}
    for _, cid, items in _blocks(text):
        hook = dict(items).get("Memory hook")
        if hook:
            hooks.setdefault(cid, []).append(hook)
    return hooks


def parse_notes(text):
    """Concept id -> the notes the learner asked to keep, oldest first.

    Every 'Note' line under any entry for the concept counts, so a note written
    before the concept has a card is kept.
    """
    notes = {}
    for _, cid, items in _blocks(text):
        for label, value in items:
            if label == "Note" and value:
                notes.setdefault(cid, []).append(value)
    return notes


def concept_state(entry, today):
    if entry is None:
        return "not-started"
    if entry["next_due"] <= today.isoformat():
        return "due"
    return entry["status"]


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{path} not found") from None
    except ValueError as e:
        raise ValueError(f"{path} is not valid JSON ({e})") from None


def _read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_model(subject_dir, today):
    subject_dir = Path(subject_dir)
    path = _read_json(subject_dir / "path.json")
    if not isinstance(path, dict) or not isinstance(path.get("domains"), list):
        raise ValueError(f"{subject_dir / 'path.json'} is not a valid path file")
    progress_file = subject_dir / "progress.json"
    progress = _read_json(progress_file) if progress_file.exists() else {}
    entries = progress.get("concepts", {}) if isinstance(progress, dict) else {}
    cards_text = _read_text(subject_dir / "cards.md")
    cards, notes = parse_cards(cards_text), parse_notes(cards_text)
    hooks = parse_hooks(_read_text(subject_dir / "misses.md"))

    counts = dict.fromkeys(STATES, 0)
    domains = []
    for d in path["domains"]:
        concepts = []
        for c in d.get("concepts", []):
            entry = entries.get(c["id"])
            if c.get("retired") or (entry and entry.get("retired")):
                continue
            state = concept_state(entry, today)
            counts[state] += 1
            concepts.append({
                "id": c["id"], "title": c.get("title") or c["id"],
                "summary": c.get("summary") or "", "state": state,
                "next_due": entry["next_due"] if entry else None,
                "doc_url": c.get("doc_url"), "card": cards.get(c["id"]),
                "hooks": hooks.get(c["id"], []), "notes": notes.get(c["id"], [])})
        domains.append({"title": d.get("title") or "", "weight_percent": d.get("weight_percent"),
                        "concepts": concepts})
    return {"title": path.get("title") or path.get("subject") or "Learning",
            "subject": path.get("subject") or "", "today": today.isoformat(),
            "source": path.get("source") or None, "counts": counts, "domains": domains}


STATE_WORDS = {"not-started": "Not started", "due": "Due now",
               "learning": "Learning", "solid": "Solid"}

CSS = """
/* Layout: one reading column; each domain is a ruled section; a finished
   concept opens into its card, an unstarted one stays a single quiet line. */
:root {
  --paper: #f6f8f7; --sheet: #ffffff; --ink: #17211f; --muted: #5d6b68;
  --rule: #d5dcda; --accent: #0b6b62;
  --due: #a85b00; --learning: #2b5fa8; --solid: #23763f; --idle: #8b9794;
  --text: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --display: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --data: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #121817; --sheet: #1a2221; --ink: #e6ecea; --muted: #9aa8a5;
    --rule: #2e3937; --accent: #5cc4b8;
    --due: #f0a94a; --learning: #7fb0f0; --solid: #6fcf8e; --idle: #6d7a77;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --paper: #121817; --sheet: #1a2221; --ink: #e6ecea; --muted: #9aa8a5;
  --rule: #2e3937; --accent: #5cc4b8;
  --due: #f0a94a; --learning: #7fb0f0; --solid: #6fcf8e; --idle: #6d7a77;
  color-scheme: dark;
}
body { background: var(--paper); color: var(--ink); font-family: var(--text);
  font-size: 1rem; line-height: 1.55; margin: 0; }
.page { max-width: 44rem; margin: 0 auto; padding-block: 2rem 4rem;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: flex; flex-direction: column; gap: 2.25rem; overflow-wrap: anywhere; }
h1, h2 { font-family: var(--display); font-weight: 600; text-wrap: balance; margin: 0; }
h1 { font-size: 1.9rem; line-height: 1.2; }
h2 { font-size: 1.25rem; line-height: 1.3; }
p, ul, dl, dd { margin: 0; }
ul { padding: 0; list-style: none; }
header { display: flex; flex-direction: column; gap: 0.6rem; }
.meta, .weight, .when, .note { color: var(--muted); font-size: 0.875rem; }
.counts { display: flex; flex-wrap: wrap; gap: 0.35rem 1.25rem; font-size: 0.9375rem; }
.counts b { font-family: var(--data); font-variant-numeric: tabular-nums; font-weight: 600; }
.domain { display: flex; flex-direction: column; gap: 0.25rem; }
.domain-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 1rem;
  justify-content: space-between; border-bottom: 2px solid var(--ink); padding-bottom: 0.4rem; }
.weight { font-family: var(--data); white-space: nowrap; }
.concept { border-bottom: 1px solid var(--rule); padding-block: 0.7rem;
  display: flex; flex-direction: column; gap: 0.5rem; }
.row { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.15rem 1rem;
  justify-content: space-between; }
.name { font-weight: 600; min-width: 0; }
.state { font-size: 0.8125rem; white-space: nowrap; display: inline-flex; align-items: baseline; gap: 0.4rem; }
.state::before { content: ""; width: 0.55rem; height: 0.55rem; border-radius: 50%;
  background: var(--idle); align-self: center; }
.s-due { color: var(--due); font-weight: 600; } .s-due::before { background: var(--due); }
.s-learning { color: var(--learning); } .s-learning::before { background: var(--learning); }
.s-solid { color: var(--solid); } .s-solid::before { background: var(--solid); }
.s-not-started { color: var(--muted); }
.s-not-started::before { background: transparent; border: 1px solid var(--idle); }
.is-not-started .name { font-weight: 400; }
.summary { color: var(--muted); font-size: 0.9375rem; max-width: 65ch; }
.card { background: var(--sheet); border: 1px solid var(--rule);
  padding: 0.9rem 1rem; display: flex; flex-direction: column; gap: 0.7rem; }
.card dl { display: flex; flex-direction: column; gap: 0.7rem; }
.card dt, .hooks-label { font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--muted); font-weight: 600; }
.card dd { max-width: 65ch; display: flex; flex-direction: column; gap: 0.5rem; }
.card table { border-collapse: collapse; width: 100%; font-size: 0.9375rem; }
.card th, .card td { text-align: left; vertical-align: top; padding: 0.35rem 0.75rem 0.35rem 0;
  border-bottom: 1px solid var(--rule); }
.card th { font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--muted); font-weight: 600; }
.card tr > :last-child { padding-right: 0; }
.hooks, .notes { display: flex; flex-direction: column; gap: 0.3rem; }
.hooks li { padding-left: 0.9rem; border-left: 2px solid var(--rule); font-style: italic; }
.notes li { padding-left: 0.9rem; border-left: 2px solid var(--accent); max-width: 65ch;
  display: flex; flex-direction: column; gap: 0.5rem; }
a { color: var(--accent); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
"""


def _e(text):
    return html.escape(str(text), quote=True)


def _link(url, label=None):
    """A link for a web address; plain text for anything else."""
    url = str(url)
    if url.startswith(("https://", "http://")):
        return f'<a href="{_e(url)}">{_e(label or url)}</a>'
    return _e(url)


def _when(concept):
    if concept["state"] == "due":
        return ""
    if concept["next_due"]:
        return f'<span class="when">back on {_e(concept["next_due"])}</span>'
    return ""


RULE_ROW = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _table_html(rows):
    """A table from markdown rows. The first row is a header only if a rule row follows it."""
    def tr(row, tag):
        return "<tr>" + "".join(f"<{tag}>{_e(c)}</{tag}>" for c in _cells(row)) + "</tr>"
    head = ""
    if len(rows) > 1 and RULE_ROW.match(rows[1]):
        head = f"<thead>{tr(rows[0], 'th')}</thead>"
        rows = rows[2:]
    body = "".join(tr(r, "td") for r in rows if not RULE_ROW.match(r))
    return f"<table>{head}<tbody>{body}</tbody></table>"


def _field_html(text):
    """A card field: plain text as it is, or paragraphs and tables if it holds table rows."""
    lines = str(text).split("\n")
    if not any(line.startswith("|") for line in lines):
        return _e(text)
    out, rows = [], []
    for line in lines + [""]:
        if line.startswith("|"):
            rows.append(line)
            continue
        if rows:
            out.append(_table_html(rows))
            rows = []
        if line:
            out.append(f"<p>{_e(line)}</p>")
    return "".join(out)


def _notes_html(concept):
    if not concept["notes"]:
        return []
    return (['<div class="hooks-label">Your notes</div><ul class="notes">']
            + [f"<li>{_field_html(n)}</li>" for n in concept["notes"]] + ["</ul>"])


def _card_html(concept):
    card = concept["card"]
    parts = ['<div class="card">', "<dl>"]
    for key, label in (("idea", "The idea"), ("shows_up", "How it shows up"),
                       ("watch_for", "Watch for")):
        if card.get(key):
            parts.append(f"<div><dt>{label}</dt><dd>{_field_html(card[key])}</dd></div>")
    parts.append("</dl>")
    if concept["hooks"]:
        parts.append('<div class="hooks-label">Memory hooks</div><ul class="hooks">')
        parts.extend(f"<li>{_e(h)}</li>" for h in concept["hooks"])
        parts.append("</ul>")
    parts.extend(_notes_html(concept))
    source = card.get("source") or concept.get("doc_url")
    if source and str(source).lower() != "none":
        parts.append(f'<p class="note">Source: {_link(source)} &middot; card written {_e(card["date"])}</p>')
    else:
        parts.append(f'<p class="note">Card written {_e(card["date"])}</p>')
    parts.append("</div>")
    return "".join(parts)


def _concept_html(concept):
    state = concept["state"]
    out = [f'<li class="concept is-{state}">', '<div class="row">',
           f'<span class="name">{_e(concept["title"])}</span>',
           f'<span class="state s-{state}">{STATE_WORDS[state]}</span>', "</div>"]
    when = _when(concept)
    if when:
        out.append(when)
    if concept["card"]:
        out.append(_card_html(concept))
    else:
        if concept["summary"]:
            out.append(f'<p class="summary">{_e(concept["summary"])}</p>')
        if concept["notes"]:
            out.append('<div class="card">' + "".join(_notes_html(concept)) + "</div>")
    out.append("</li>")
    return "".join(out)


def render_html(model):
    """The page, in the form an Artifact publish expects: title, style, then content."""
    title = " ".join(str(model["title"]).split()[:4])
    counts = model["counts"]
    has_cards = any(c["card"] for d in model["domains"] for c in d["concepts"])
    out = [f"<title>{_e(title)}</title>",
           '<meta name="claude:viewport-fit-sides" content="cover">',
           f"<style>{CSS}</style>", '<div class="page">', "<header>",
           f'<h1>{_e(model["title"])}</h1>']
    meta = f'As of {_e(model["today"])}'
    source = model.get("source")
    if source and source.get("fetched"):
        outline = _link(source.get("url") or "", "Outline") if source.get("url") else "Outline"
        meta += f' &middot; {outline} fetched {_e(source["fetched"])}'
    out.append(f'<p class="meta">{meta}</p>')
    out.append('<p class="counts">' + "".join(
        f"<span><b>{counts[s]}</b> {label}</span>" for s, label in
        (("due", "due now"), ("learning", "learning"), ("solid", "solid"),
         ("not-started", "not started"))) + "</p>")
    if not has_cards:
        out.append('<p class="note">No cards yet. A card is added each time a concept is finished.</p>')
    out.append("</header>")
    for d in model["domains"]:
        if not d["concepts"]:
            continue
        out.append('<section class="domain"><div class="domain-head">')
        out.append(f'<h2>{_e(d["title"])}</h2>')
        if d["weight_percent"] is not None:
            out.append(f'<span class="weight">{_e(d["weight_percent"])}% of the exam</span>')
        out.append("</div><ul>")
        out.extend(_concept_html(c) for c in d["concepts"])
        out.append("</ul></section>")
    out.append("</div>")
    page = "\n".join(out) + "\n"
    return page.encode("ascii", "xmlcharrefreplace").decode("ascii")


def _iso_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {text!r}") from None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="build_page.py")
    parser.add_argument("subject_dir")
    parser.add_argument("--today", type=_iso_date, default=None)
    args = parser.parse_args(argv)
    subject_dir = Path(args.subject_dir)
    try:
        model = build_model(subject_dir, args.today or date.today())
        page = render_html(model)
        out = subject_dir / "page.html"
        tmp = subject_dir / "page.html.tmp"
        with open(tmp, "w", encoding="ascii") as f:
            f.write(page)
        os.replace(tmp, out)
    except (ValueError, KeyError, TypeError, OSError) as e:
        print(str(e).replace("\n", " "), file=sys.stderr)
        return 1
    concepts = [c for d in model["domains"] for c in d["concepts"]]
    print(json.dumps({"page": str(out.resolve()), "concepts": len(concepts),
                      "cards": sum(1 for c in concepts if c["card"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
