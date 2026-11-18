# Subject setup

Read this when a learner names a subject they have no folder for (or a folder with no `path.json`), or when a certification path needs its exam guide fetched again (section 6). File shapes are in `data-files.md`. Run the script the way `SKILL.md` says, with `--today` when a date was given.

## 1. Setup questions

Ask these one at a time, one per turn. Skip any the learner has already answered, in this conversation or in `profile.json`.

1. **Goal:** what do they want to be able to do? For a certification: pass the exam, or use the skills at work?
2. **Deadline:** is there an exam date or target date? "None" is a fine answer; record `null`.
3. **What they already know:** about this subject, in their own words.
4. **Session length:** how many minutes a session should run. Ask only if `profile.json` has no `session_minutes` yet.

Also ask whether they have their own material (notes, a course, a book) to learn from. If they point at a file or folder, set `material_path` to it. For a certification the path is still `certification`, built from the official exam guide, because the exam follows the guide, not the material. For any other subject the path is `supplied`.

Write the answers back: `goal` and `deadline` go in `path.json`; anything new about goals, background, or session length goes in `profile.json`.

## 2. Choose the kind

| The subject is | `kind` |
|---|---|
| A vendor certification or exam with a published official guide (AWS, Google Cloud, Azure, and so on), with or without the learner's own material | `certification` |
| Not a certification, and the learner pointed at their own material | `supplied` |
| Anything else (maths, science, a language, a skill) | `general` |

Pick a subject id: lowercase with hyphens, short, such as `aws-saa` or `fractions`. It is both the folder name and `path.json`'s `subject`.

Now create the subject folder inside the learner's folder, and run `init` on it. Remember what `init` printed: section 3 needs it.

- `{"created": true}`: a new subject. Carry on.
- `{"created": false}` and the folder has a `path.json`: this subject already exists. Stop setup, and run the session as an existing subject (`SKILL.md`, Start of every session, step 6). Setting it up again could overwrite the learner's records.
- `{"created": false}` and no `path.json`: an earlier setup did not finish. Carry on with setup in this folder. Keep any files already in it.

Then run `due` on it. `due` is the only command that prints `today`, and it is the date to use for everything you write during setup, including `source.fetched`.

## 3. Build the path

### certification

The exam changes over time, and a learner who learns an old syllabus loses marks. So build from the vendor's current documents, not from memory.

1. Search the web for the vendor's current official exam guide for this exam. Prefer the vendor's own site over third-party summaries.
2. Fetch it. Set `source.url` to the guide's address and `source.fetched` to today's date (the `today` value that `due` printed).
3. Take the domains and their weightings from the guide. Each guide domain becomes one path domain, with `weight_percent` from the guide.
4. Before the first documentation fetch, write a short message to the learner, then start fetching in the same turn. Say that you are about to read the official documentation for the services the guide names, roughly how many pages, and that it will take a few minutes. Several minutes of silence looks like a hang.
5. Read the documentation before you build any concepts. For each service or topic the guide's task statements name (not its appendix list of in-scope services), fetch one official documentation overview page: one page per service or topic, not one per concept. For a foundational exam that is roughly 20 to 40 pages, a few minutes of reading. Do not show the outline (section 4) until this reading is done: concepts built from memory are what this step prevents. Build each service's concepts from the guide and its page: what the exam tests about it, its defaults, its limits, and what people commonly confuse it with.
6. Set `doc_url` only to a page you actually fetched, copying its address exactly as you fetched it; never write an address from memory, even one that looks right. A concept whose page you did not fetch gets `doc_url: null`, because a link nobody read is a guess that looks verified. After writing `path.json`, check every non-null `doc_url` against the addresses you fetched, and set any that does not match to `null`. Before a certification concept is taught, its page is fetched and a null `doc_url` is filled (`SKILL.md`, Session order).
7. If the guide or documentation mentions renamed products, add them to `renamed_products`.
8. Tell the learner plainly: the guide is an outline, not the whole exam, and questions can reach into detail it does not list.

**If the guide cannot be fetched** (no web access, page gone, blocked): say so plainly. Offer to build the path from your own knowledge instead, with `source` set to `null`. If they agree, tell them the path is unverified and may not match the current exam, and set `doc_url` only for links you have actually checked. Do not present it as current. Each later session will offer to fetch the guide again (section 6). If they decline, stop setup, and suggest they try again when the guide can be reached. Delete the subject folder only if `init` printed `{"created": true}` in this session and the folder holds nothing but `progress.json`; then nothing is lost. Otherwise leave the folder as it is, because it may hold records from an earlier session.

### general

Build from your own knowledge. Order concepts so each one rests on earlier ones. `source`, `weight_percent` and `doc_url` are `null`.

### supplied

For non-certification subjects only. Read the material. Build the path from it only, in its order where it has one, and set `material_path`. Do not add topics it does not cover. A certification with the learner's own material is built as `certification` above, with `material_path` set; its material is taught from, but the official documentation outranks it: where they conflict, teach the documentation and tell the learner.

### Size, for every kind

- 3 to 8 domains.
- Each concept small enough to teach in about ten minutes: one idea, which can be guessed at, taught with one example, and questioned.
- Concept ids are lowercase with hyphens and unique across the whole path. Once written, an id is never renamed, reused, or deleted, because progress is keyed by it.

## 4. Show the outline and write the files

1. Show the path in outline: domains (with weightings for a certification), and concept titles under each. Keep it scannable.
2. Ask whether they want to skip, reorder, or trim anything. Apply what they ask to the outline.
3. Write `path.json` in the subject folder. Never overwrite an existing `path.json`: if one is there, this is an existing subject (section 2), so stop setup.
4. For each concept the learner explicitly asked to skip, run `start <id> known`, without testing it. It comes back in 16 days for one check. This is the same as skipping later in a session.
5. Create empty `misses.md` and `sessions.md` files, each only if it is not already there. An unfinished earlier setup may have left one, and it may hold notes.

## 5. Placement check

A short check, so the tutor does not re-teach what the learner already has. It covers only concepts the learner did not explicitly skip in section 4.

- Ask at most eight questions in all, spread across domains, one per turn.
- Start with the hardest domains the learner said they already know. If they say they know nothing yet, skip the check.
- Use reasoning questions from the teaching method, and ask for confidence after each, before any feedback.
- Give no teaching during the check. Say briefly whether each answer was right, then move on.
- A `good` answer given as `sure` marks that concept known: run `start <id> known`. It comes back in 16 days to be checked once.
- Anything else leaves the concept with no entry. It will be taught in order. Do not run `start` or `record` for it, and do not log it in `misses.md`.

Then tell the learner what the first new concept is, and begin the session as `SKILL.md` describes.

## 6. Re-checking a certification path

Offer once at the start of the session to fetch the exam guide when either is true:

- `due` prints a `source_age_days` above 90.
- `kind` is `certification` and `source` is `null`: the path was built without the guide and is unverified.

If the learner says no, carry on with the session.

If they say yes:

1. Fetch the current guide, as in section 3, using the `today` from this session's `due`. Before fetching the guide, and before reading documentation pages for any new services, tell the learner first what you are about to read and how long it will take, as in section 3 step 4.
2. Compare it with `path.json`. Show the learner what differs: new domains or topics, dropped ones, changed weightings. For an unverified path, also say which concepts the guide confirms.
3. On their say-so:
   - Add new concepts to `path.json`, in their place in the order. They have no progress entry, so they count as not started.
   - For each dropped concept, set `"retired": true` on it in `path.json`. If it has a progress entry, also run `retire <id>`. If it has none, `retire` would fail, so only set the flag in `path.json`.
   - Update weightings, and set `source.url` and `source.fetched` to the new guide and today's date.
4. Never delete or rename a concept id. Progress is keyed by id, so existing records carry over untouched.

If the re-fetch fails, say so, keep the existing path, and tell the learner the date it was last fetched, or that it is still unverified if it never was.
