# Claude Skills

Skills for [Claude Code](https://claude.com/claude-code). Each folder is one skill and can be installed on its own.

| Skill | What it does |
|---|---|
| [socratic-tutor](socratic-tutor/) | Tutors you on a subject over several sessions. It teaches one small concept at a time, questions you until you can reason it out, and brings concepts back for revision on a spaced schedule. |

## Install a skill

You need Claude Code and Python 3.9 or later. The skills use only the Python standard library.

```bash
git clone https://github.com/hitesh-yadav-x/claude-skills.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/claude-skills/socratic-tutor" ~/.claude/skills/socratic-tutor
```

The link means `git pull` updates the skill. To install a fixed copy, copy the folder to `~/.claude/skills/` in place of the link. Start a new Claude Code session afterwards.

## socratic-tutor

Start a session by asking for a subject:

```
/socratic-tutor AWS Certified Solutions Architect - Associate
```

or in plain words: "tutor me on fractions", "continue my learning", "what's due".

What to expect:

- **Setup, once per subject.** The tutor asks your goal and how long your sessions are, builds a path of concepts, and checks what you already know. For a certification it builds the path from the official exam guide and teaches from the official documentation, with links.
- **Each concept.** You guess first, the tutor teaches briefly, then questions you and asks how sure you are. You explain the idea back, and you get a short card to keep.
- **Revision.** Concepts come back after 1, 3, 7, 16 and 35 days. A weak answer brings a concept back sooner.
- **Things you can say at any time:** `pause`, `stop`, `skip`, `slower`, `faster`, "just tell me", "how am I doing", "show my cards", "add that to my card".

### Where your records are kept

Everything is in plain files under `~/learning/`, one folder per learner and subject. Set `SOCRATIC_TUTOR_HOME` to use another folder. `socratic-tutor/references/data-files.md` describes every file, and `socratic-tutor/examples/sample-learner/` holds a small example.

At the end of each session the tutor builds `page.html` in the subject folder, showing your path, progress and cards. It asks once whether you also want that page published as a private page on claude.ai. If you say no, nothing leaves your computer.

### Run the tests

```bash
cd socratic-tutor
python3 -m unittest discover -s tests
```

## Licence

MIT. See [LICENSE](LICENSE).
