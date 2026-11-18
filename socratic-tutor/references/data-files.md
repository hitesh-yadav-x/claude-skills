# Data files

Everything the tutor remembers lives in plain files. This page documents every file and field, and the revision rules in full, so another program can read and write the same records.

## Folder layout

```
~/learning/                     data root
  <learner>/
    profile.json                level, goals, session length, age range, what explanations work
    <subject>/
      path.json                 ordered domains and concepts, exam weightings, source link and fetch date
      progress.json             one entry per concept
      misses.md                 one entry per miss
      cards.md                  one card per finished concept
      sessions.md               dated notes per session, plus the resume note after a pause
      page.html                 the learner's page, built from the files above; safe to delete
```

A worked example is in `examples/sample-learner/`.

## Which learner

The data root is `$SOCRATIC_TUTOR_HOME` if that variable is set, otherwise `~/learning/`.

A learner folder is a folder in the root that holds `profile.json`. `~/learning` is a common folder name, so other folders may be there; a folder without `profile.json` is not a learner. Never adopt it or give it a profile.

| Learner folders in the root | What to do |
|---|---|
| One | Use it without asking. |
| None | Create one from the learner's first name, with a new `profile.json`. |
| Several | Ask who is studying. |

`schedule.py` never looks for the root. It is given the subject folder as an argument.

## Rules for every JSON file

- `"schema_version": 1` is the first key.
- Dates are `YYYY-MM-DD`.
- A field with no value is `null`, not missing.

## profile.json

```json
{"schema_version": 1, "name": "", "age_range": "child|teen|adult",
 "session_minutes": 20, "goals": [""], "background": "",
 "explanation_notes": [""], "page": "yes|no|null"}
```

| Field | Meaning |
|---|---|
| `name` | The learner's first name. |
| `age_range` | One of `child`, `teen`, `adult`. Sets tone and vocabulary. |
| `session_minutes` | How long a session should run. |
| `goals` | Why they are learning, in their words. |
| `background` | What they already know, and their job or schooling if it helps. |
| `explanation_notes` | What kinds of explanation worked or failed for them. Add one when you notice. |
| `page` | `"yes"` if the learner wants a page for each of their subjects published on claude.ai, where only the signed-in account can see it; `"no"` if not; `null` if they have not been asked. A missing field means `null`. They can change it at any time. |

## path.json

```json
{"schema_version": 1, "subject": "aws-saa", "title": "",
 "kind": "certification|general|supplied",
 "goal": "", "deadline": "YYYY-MM-DD or null",
 "source": {"url": "", "fetched": "YYYY-MM-DD"},
 "material_path": "path or null",
 "page_url": "link or null",
 "renamed_products": [{"old": "", "new": ""}],
 "domains": [{"id": "", "title": "", "weight_percent": 0,
   "concepts": [{"id": "", "title": "", "summary": "", "doc_url": "", "retired": false}]}]}
```

| Field | Meaning |
|---|---|
| `subject` | Subject id. Matches the folder name. |
| `title` | Display name. |
| `kind` | `certification` (built from an official exam guide), `general` (built from what you know), or `supplied` (a non-certification subject built from the learner's own material). A certification is always `certification`, even when the learner has their own material. |
| `goal` | What the learner wants to be able to do. |
| `deadline` | Exam or target date, or `null`. |
| `source` | Where the outline came from: `url`, and `fetched`, the date it was fetched. `null` for `general` and `supplied`. |
| `material_path` | Path to the learner's own material, or `null`. |
| `page_url` | Link to this subject's published page, or `null` if it has not been published. A missing field means `null`. |
| `renamed_products` | Old and new names for products renamed since older material was written. Empty list if none. |
| `domains` | Ordered list of topic areas. |
| `domains[].id`, `title` | Short id and display name. |
| `domains[].weight_percent` | Exam weighting. `null` outside certifications. |
| `domains[].concepts` | Ordered list of concepts in that domain. |
| `concepts[].id` | Lowercase with hyphens. Unique across the whole path. Never reused or renamed once created. |
| `concepts[].title`, `summary` | Display name and one-sentence description. |
| `concepts[].doc_url` | Official documentation link, set only to a page that was actually fetched. `null` outside certifications, and for a certification concept whose page has not been read yet. |
| `concepts[].retired` | `true` when the concept was dropped from the outline. The concept stays in the file. |

`schedule.py due` reads only `source.fetched`, to report `source_age_days`.

## progress.json

Written only by `schedule.py`. Never edit it by hand.

```json
{"schema_version": 1,
 "concepts": {
   "adding-fractions": {
     "status": "learning", "step": 0, "streak": 0,
     "misconception": true, "retired": false,
     "last_reviewed": "2026-11-13", "next_due": "2026-11-14"}}}
```

| Field | Meaning |
|---|---|
| key | Concept id from `path.json`. A concept has an entry once it has been started. |
| `status` | `learning` or `solid`. (`new` means no entry yet; the script never writes it.) |
| `step` | Position on the gap ladder, 0 to 4. |
| `streak` | Good answers in a row. |
| `misconception` | `true` after a confident wrong answer. Cleared by the next good answer. |
| `retired` | `true` when the concept is retired. Retired concepts are never due. |
| `last_reviewed` | Date of the last start or answer. |
| `next_due` | Date the concept is next due. |

## misses.md

Appended to, newest last. One entry per miss.

```markdown
## 2026-11-16 · s3-storage-classes
- Question: ...
- Their answer: ...
- Their reasoning: ...
- Confidence: guess | fairly-sure | sure
- Why it was wrong: ...
- Memory hook: ...
```

| Part | Meaning |
|---|---|
| Heading | Date, then the concept id. |
| Question | The question as asked. |
| Their answer | What they said. |
| Their reasoning | Why they said it, in their words. |
| Confidence | How sure they said they were. |
| Why it was wrong | The gap in understanding. For a right guess: that it had no reason behind it. |
| Memory hook | One short line that will help them remember. |

Before revising a concept, read its entries and aim questions at them. Log an entry for every `partial` or `poor` answer and every right answer given as a `guess`, as it happens. The `log_miss` value that `schedule.py record` prints is only a cross-check (see When the commands are called).

## cards.md

One card per finished concept: a short record of what the learner worked out, to reread later.

```markdown
## 2026-11-16 · adding-fractions
- The idea: ...
- How it shows up: ...
- Watch for: ...
- Source: ...
- Note: ...
```

| Part | Meaning |
|---|---|
| Heading | The date the card was written, then the concept id. Same form as `misses.md`. |
| The idea | The concept in two or three plain sentences. |
| How it shows up | How an exam question or a real problem presents it, and the usual trap. |
| Watch for | This learner's own weak point on it, or "nothing yet". |
| Source | Official documentation link. Certifications only; leave the line out otherwise. |
| Note | Something the tutor said that the learner asked to keep. Only when asked; any number of lines, one note each. |

A card is written when a new concept is finished, straight after its `start <id> taught` or `start <id> explained`. A concept started as `known` has no card at first. A fresh card is also written when a revision concept had to be taught again, after its `record`: it replaces the concept's entry, or is added if the concept had none. A concept has one entry. If two are ever present, the later one in the file is the one in force.

Write each field on one line, with the plain labels above. A field may also hold a table: put its rows on the lines under the field, each starting with `|`, with a `|---|---|` row under the header row. A line of text after the table goes on its own line. Use a table only when the learner asks for one, or the card holds a list they need to compare. The page builder also reads bold labels, `*` bullets and wrapped lines, but a block in which it finds none of the first three fields is not treated as a card, and the page shows the concept's summary instead.

A `Note` line is added when the learner asks to keep something the tutor said, at any point in a session. It goes after the entry's other lines, in the tutor's words, one or two sentences, with the documentation link for a certification fact. If the concept has no entry yet, the entry is created with its heading and the note alone, and the card's fields are written into that entry when the concept is finished. Notes are kept when a card is replaced. The page builder collects the notes from every entry for a concept, oldest first, so a note is never lost to a second entry.

Memory hooks are not copied into a card. The page reads them from `misses.md`, so they stay current as revision adds more.

## sessions.md

Appended to, newest last.

```markdown
## 2026-11-16
- Revised: ...
- New: ...
- Solid: ...
- Shaky: ...
- Next: ...

### Resume note
(only after a pause: the concept, the step reached, the last question asked, explained directly: yes/no, confident wrong answer: yes/no)
```

| Part | Meaning |
|---|---|
| Heading | Session date. |
| Revised | Concepts revised this session. |
| New | Concepts taught for the first time. |
| Solid | Concepts that now feel secure. |
| Shaky | Concepts that need more work, and why. |
| Next | What to do next session. |
| Resume note | Written only when the learner pauses mid-concept. The next session picks it up, and deletes it at that concept's Close, once the concept has been sent to the script. Deleting it at pickup would lose its two scoring facts if that session ended before Close. |

## Who writes which file

| File | Written by |
|---|---|
| `profile.json`, `path.json`, `misses.md`, `cards.md`, `sessions.md` | Claude, directly. |
| `progress.json` | `schedule.py` only. |
| `page.html` | `build_page.py` only. |

## schedule.py commands

Run with `python3 scripts/schedule.py`. Every command takes the subject folder first. Every command takes optional `--today YYYY-MM-DD`, which replaces the real date. Use it whenever a date to use as today has been stated, in tests or by the learner, and pass the same date on every command in that session. Output is one line of JSON. On an error, the message goes to stderr and the exit code is 1.

| Command | Does | Example | Output |
|---|---|---|---|
| `init` | Creates `progress.json` with no concepts. Does nothing if it exists. | `schedule.py init ~/learning/maya/fractions` | `{"created": true}` or `{"created": false}` |
| `start <id> <how>` | Adds a concept. `how` is `taught` (learner got there by questions), `explained` (tutor had to explain it), or `known` (placement check or skipped). Fails if already started. | `schedule.py start DIR adding-fractions taught` | The new entry. |
| `record <id> <result> --confidence <c>` | Applies an answer. `result` is `good`, `partial` or `poor`. `c` is `guess`, `fairly-sure` or `sure`. Fails if not started or retired. | `schedule.py record DIR adding-fractions poor --confidence sure` | The updated entry, plus `effective_result` and `log_miss`. |
| `due` | Lists what to revise. | `schedule.py due DIR` | `{"today", "due", "misconceptions", "source_age_days"}` |
| `summary` | Counts concepts. | `schedule.py summary DIR` | `{"new", "learning", "solid", "retired", "due"}` |
| `retire <id>` | Marks a concept retired. Fails if not started. | `schedule.py retire DIR old-concept` | The updated entry. |

Notes on the output:

- `due` is the ids due today or earlier, oldest first. Retired concepts are left out.
- `misconceptions` is the ids with `misconception` true, not retired.
- `source_age_days` is days since `source.fetched` in `path.json`, or `null` if there is no source. Offer to re-check the exam guide when it passes 90.
- `summary` counts retired concepts under `retired` only. `new` is always 0 because the script writes no `new` entries; count path concepts with no entry as new yourself.
- `effective_result` is the result after the confidence adjustment. `log_miss` is `true` when the answer sent was a miss. Misses are logged as they happen, so this is only a cross-check that `misses.md` has them.

## build_page.py

`python3 scripts/build_page.py <subject folder> [--today YYYY-MM-DD]` writes `page.html` in the subject folder. It reads `path.json`, `progress.json`, `cards.md` and `misses.md`, and changes none of them. `cards.md`, `misses.md` and `progress.json` may be absent.

Output is one line of JSON: `{"page": "<full path>", "concepts": <count>, "cards": <count>}`. On an error, such as a missing or invalid `path.json`, the message goes to stderr, the exit code is 1, and no page is written.

The page shows each domain, with its weighting if it has one, and each concept that is not retired, with one of four states:

| State | When |
|---|---|
| Not started | The concept has no progress entry. |
| Due now | `next_due` is on or before today. |
| Learning | Not due, and `status` is `learning`. |
| Solid | Not due, and `status` is `solid`. |

A concept retired in `path.json` or in `progress.json` is left off the page and out of its counts. A concept with a card shows the card, its memory hooks from `misses.md`, the learner's notes, and its source link. A concept without one shows its summary, and its notes if it has any.

`page.html` has no `<html>`, `<head>` or `<body>` tags of its own, because a published page is given them when it is published. It still opens in a browser as it is.

## When the commands are called

Individual answers are not sent to the script one by one. Each concept is sent once per session, as below. Sending every answer would climb the ladder several steps in one sitting, and the gaps would stop meaning anything.

**A new concept** gets one `start`, after it is finished (its Close step):

- `start <id> taught`: the learner reached it through questions.
- `start <id> explained`: the tutor had to explain directly at any point, or the learner asked for the answer.
- `start <id> known`: the learner skipped it, or a placement check showed they know it. It is not taught or tested.
- If any scored answer on it was wrong and given as `sure`, also run `record <id> poor --confidence sure` straight after `start`. This sets the misconception flag, so the concept gets extra questions next time.

A new concept starts at the bottom of the ladder whatever happens, so per-answer records would only add noise. What matters is how it was reached, and whether a wrong belief showed up. An unfinished new concept (the learner paused or stopped) is not sent.

**A revision concept** gets one `record` per session, after its last question: `record <id> <result> --confidence <c>`.

- `<result>` is the weakest judgment among its scored answers (`poor` below `partial` below `good`).
- `<c>` is the lowest confidence the learner gave on it (`guess` below `fairly-sure` below `sure`). When no confidence was given, because the learner said they did not know, send `guess`.
- One exception: if any scored answer on it was wrong and given as `sure`, send `record <id> poor --confidence sure`, so the misconception flag is set even if a later answer was given as a guess.
- A revision concept the learner skips gets nothing. It stays due.

**Misses** are written to `misses.md` as they happen, not when the script is called: one entry for every `partial` or `poor` answer and every right answer given as a `guess`. `log_miss` in the `record` output is only a cross-check: when it is `true`, check every miss on that concept is in `misses.md`, and add any that is not.

## Revision rules

Reimplement these exactly.

**Gap ladder:** 1, 3, 7, 16, 35 days. `step` is the index, 0 to 4. After any start or answer, `last_reviewed` is today and `next_due` is today plus the ladder gap for the (new) step.

**Starting a concept:**

| How | status | step | streak | Due |
|---|---|---|---|---|
| `taught` or `explained` | `learning` | 0 | 0 | Tomorrow |
| `known` | `solid` | 3 | 3 | In 16 days |

`misconception` and `retired` start `false`. A `known` concept is checked once, at 16 days. If that check is poor, the concept drops to `learning` and is taught normally.

**Confidence adjusts the result first:**

| Answer | Confidence | Counts as | Log a miss | Sets `misconception` |
|---|---|---|---|---|
| good | `guess` | partial | Yes | No |
| good | `fairly-sure` or `sure` | good | No | No |
| partial | any | partial | Yes | No |
| poor | `sure` | poor | Yes | Yes |
| poor | `guess` or `fairly-sure` | poor | Yes | No |

A partial or poor answer is always logged as a miss. After a `sure` poor answer, spend extra questions on that concept in that session and the next.

**Then apply the adjusted result:**

| Result | Step | Streak | Status | Misconception |
|---|---|---|---|---|
| good | Up one, capped at 4 (35 days) | +1 | `solid` when streak reaches 3, else unchanged | Cleared |
| partial | Unchanged | Unchanged | Unchanged | Unchanged |
| poor | Back to 0 (due tomorrow) | 0 | `learning` | Set if the poor answer was `sure`, else unchanged |

`solid` is a label, not a jump. A solid concept keeps climbing one step at a time and stays at 35 days once there. A partial answer keeps the step but still moves `next_due` to today plus the gap for that step.

**Due:** a concept is due when it is not retired and `next_due` is on or before today.
