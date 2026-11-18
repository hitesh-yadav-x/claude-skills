# Session scenarios

Study sessions run against the skill, to check it behaves as the design says when a real conversation happens. The unit tests check `schedule.py`; these check the instructions.

## How they were run

- The skill was not installed. For each scenario a fresh tutor agent (Claude Sonnet) was told the skill had triggered, pointed at this folder's `SKILL.md`, given the data root as `SOCRATIC_TUTOR_HOME`, and told today's date. It was told nothing about what was being tested.
- The learner was played turn by turn from the script below. Learner messages were kept short and gave no hints.
- Every scenario used its own fresh data folder under a temporary directory, never `~/learning`. Scenarios that need an existing learner were seeded with a copy of the folder an earlier scenario left behind, as stated in each one. A later session always used a fresh tutor agent, because a real later session starts with no memory.
- First-session date: 2026-11-16. Scenario 5's later session: 2026-11-20.
- Each condition was judged from the tutor's replies and from the files left in the data folder. Which command was run was judged from the resulting `progress.json` entry.

## Scenarios

| # | Scenario | Passes when |
|---|---|---|
| 1 | New learner asks to learn fractions | Setup questions come one per turn; a path is shown before anything is taught; `profile.json`, `path.json`, `progress.json` exist and parse |
| 2 | First concept, learner answers well | Guess questions come before any explanation; every scored question is followed by a confidence ask; an explain-back is requested; `start <id> taught` was run |
| 3 | Learner gives a wrong answer and says they are sure | The tutor's next turn is a question, not the answer; a `misses.md` entry with all six fields is written |
| 4 | Learner stays stuck through three guiding questions | The tutor explains directly by the fourth turn at the latest, asks one confirming question, and the concept is started as `explained` |
| 5 | Session resumed with `--today` four days later (set the date by telling the tutor to pass `--today`) | The session opens with revision of due concepts before new material; the revision question differs from the original |
| 6 | Learner says "pause" mid-concept, then returns | A resume note is written; the next session continues that concept and removes the note |
| 7 | New learner asks to prepare for AWS Cloud Practitioner | The official exam guide is fetched; `source.url` and `source.fetched` are set; domain weights are present; taught facts carry documentation links; the learner is told the guide is not the whole exam |
| 8 | "How am I doing?" | A short text answer with counts that match `schedule.py summary`; no page is generated |
| 9 | A new concept is finished (added with learning cards) | One entry for the concept is in `cards.md`, in the shape in `data-files.md`; the same card is shown to the learner; it holds no fact that was not taught or tested; a concept the learner skipped has no card |
| 10 | A session ends and `page` is not set in `profile.json` (added with the page) | The tutor asks once about the page and names claude.ai; the answer is written to `profile.json`; `page.html` is in the subject folder whatever the answer; with "no", nothing is published |

## Results

Evidence for "which command was run": `taught` and `explained` produce identical `progress.json` entries by design (both start at step 0, due tomorrow), so the entry alone cannot tell them apart. For those conditions the command line was also read from the tutor agent's own tool log, and is quoted below.

### 1. New learner asks to learn fractions

Data folder: empty. First message: "I want to learn fractions".

Learner script: "Sam" / "I'm an adult. I want to be able to help my daughter with her homework, and stop feeling lost when fractions come up." / "No date, just whenever." / "I get halves and quarters, like half a pizza. But adding them or anything with different numbers on the bottom loses me." / "20 is fine." / "No, nothing." / "Looks good, keep it as is."

| Condition | Result | Evidence |
|---|---|---|
| Setup questions one per turn | pass | Five separate turns: goal ("what do you want to be able to do with fractions?"), deadline ("Is there a date you're aiming for"), knowledge ("what do you already know about fractions?"), length ("How many minutes would you like a session to run?"), material ("do you have any material of your own"). Each turn asked one. |
| Path shown before anything is taught | pass | Outline of five domains shown, then "Would you like to skip, reorder, or trim anything?"; next turn began the placement check ("I won't teach during these"). |
| `profile.json`, `path.json`, `progress.json` exist and parse | pass | All three under `sam/` and `sam/fractions/`, each parsed with `python3 -m json.tool`; `path.json` has `kind: general`, 5 domains, 11 concepts; `progress.json` has `concepts: {}`. |

This folder, as it stood after the outline was accepted (before any placement answer), was kept as the seed for scenarios 2, 3, 4 and 6.

### 2. First concept, learner answers well

Data folder: copy of the scenario 1 seed. Date 2026-11-16. First message: "Can we do a fractions session?"

Learner script: "3/8. The 3 is the slices I ate, and the 8 is how many slices the whole pizza was cut into." / "3 slices from the one cut into 4. Fewer cuts means each slice is bigger, so 3 big slices is more pizza than 3 small ones." / "Sure." / "It gets smaller. The same pizza is being cut into 10 pieces instead of 4, so each piece has to be thinner." / "Sure." / (explain back) "The bottom number says how many equal pieces the whole thing is cut into, so it tells you how big each piece is. The top number counts how many of those pieces you've got." / "stop".

| Condition | Result | Evidence |
|---|---|---|
| Guess before any explanation | pass | First tutor turn: "Before I explain anything, take a guess. Say a pizza is cut into 8 equal slices and you eat 3 of them..."; the explanation came only in the next turn. |
| Every scored question followed by a confidence ask | pass | Both scored questions were followed by "How sure are you of that one: was it a guess, fairly sure, or sure?" before any feedback. |
| Explain-back requested | pass | "Last step for this idea. In your own words, what do the top and bottom numbers of a fraction tell you?" |
| `start <id> taught` was run | pass | Tool log: `schedule.py start $SOCRATIC_TUTOR_HOME/sam/fractions top-and-bottom taught --today 2026-11-16`; entry `learning`, step 0, due 2026-11-17; no other command on it. |

### 3. Wrong answer given as sure

Data folder: copy of the scenario 1 seed. Date 2026-11-16. First message: "Can we do a fractions session?"

Learner script: "3/8? 3 is what I ate and 8 is how many slices there were." / "The slice from the one cut into 8, because 8 is a bigger number than 4." / "Sure." / "With 4 friends, they each get more. Oh. So the slice from the pizza cut into 4 is bigger." / "Fairly sure now." / then right answers through to the explain-back.

| Condition | Result | Evidence |
|---|---|---|
| Next turn is a question, not the answer | pass | After "Sure." the tutor replied: "Imagine one pizza and 8 friends who all get an equal share. Then imagine the same pizza shared between just 4 friends. In which case does each friend get the bigger piece?" It did not state which slice was bigger. |
| `misses.md` entry with all six fields | pass | Entry `## 2026-11-16 · top-and-bottom` with Question, Their answer ("The slice from the one cut into 8."), Their reasoning ("8 is a bigger number than 4"), Confidence (`sure`), Why it was wrong, Memory hook ("more slices, smaller slices"). |

Also seen: tool log shows `start ... top-and-bottom taught` then `record ... top-and-bottom poor --confidence sure`; `misconception: true` in `progress.json`.

### 4. Learner stays stuck

Data folder: copy of the scenario 1 seed. Date 2026-11-16. First message: "Can we do a fractions session?"

Learner script: "3/8 I think, and the 8 is the total?" / "One eighth? Because 8 is bigger than 5." / "Not really sure." / "Bigger? 10 is more than 2." / "With 9 people there'd be more slices, so... more pizza? I don't know." / (after the explanation) "1/4, because the cake is only cut into 4 so each piece is bigger than when it's cut into 10." / "Fairly sure." / then right answers through to the explain-back.

| Condition | Result | Evidence |
|---|---|---|
| Explains directly by the fourth turn at the latest | pass | Turns after the miss: confidence ask, guiding 1 ("shared between 10 people, is each person's slice bigger or smaller"), guiding 2 ("share it with 1 other person or with 9"), then turn 4: "Let me explain this one directly, since the hints haven't helped." |
| One confirming question | pass | Same turn: "Now a fresh one to check it landed. Which is bigger, 1/4 of a cake or 1/10 of the same cake, and why?" |
| Started as `explained` | pass | Tool log: `schedule.py start .../s4/sam/fractions top-and-bottom explained --today 2026-11-16`. |

Not a pass condition, but wrong: the tutor judged the confirming question `poor` and wrote a second `misses.md` entry for it, with "Why it was wrong: Not wrong. Judged poor because the idea ... was reached by direct explanation". That entry has no gap to aim revision at. Cause: teaching-method section 4 said "When you had to explain directly, judge that question `poor`", right after the sentence about asking a fresh question, so "that question" read as the fresh one. The worked dialogue's note ("Explain directly, then ask a fresh question. This question is judged `poor`.") had the same ambiguity.

Fix (round 1): teaching-method section 4 now says "judge the question they missed `poor`, whatever the learner's first answer to it was ... The fresh confirming question is judged on its own answer, like any other scored question; a right answer to it is not a miss." The worked-dialogue note now says "The question they missed is judged `poor`; the fresh one is judged on its own answer." `SKILL.md`'s scoring paragraph adds "the fresh question you ask after explaining is judged on its own answer."

Re-run (fresh tutor, fresh copy of the seed, same learner script with equivalent wording): explained directly on turn 4 ("I'll explain this one directly, since the questions haven't got you there."), one confirming question ("Which is bigger, 1/3 of a cake or 1/5 of the same cake, and why?"), tool log `start ... top-and-bottom explained --today 2026-11-16`. `misses.md` now holds one entry, for the missed question only. All three conditions pass.

### 5. Later session, four days on

Data folder: copy of scenario 2's folder after its session (top-and-bottom started 2026-11-16, due 2026-11-17; one `sessions.md` entry). Fresh tutor told "Today's date is 2026-11-20". First message: "Let's carry on with fractions".

Learner script: "I'd say it's the other way round. 8 means the pizza is cut into more slices, so each one is smaller. 1/4 is bigger." / "Sure."

| Condition | Result | Evidence |
|---|---|---|
| Opens with revision of due concepts before new material | pass | First turn: "Before we start something new, here's a quick check on what we did last time." New material ("On to something new. Before I explain anything, take a guess") came only after it was recorded. |
| Revision question differs from the original | pass | Revision: "Your daughter tells you, '1/8 of a pizza is bigger than 1/4, because 8 is bigger than 4.' What would you say to her". Scenario 2 asked 3 slices of 4 vs of 8, and 1/4 vs 1/10; neither was repeated. |

Also seen: `--today` was passed. Tool log: `schedule.py due ... --today 2026-11-20` and `record ... top-and-bottom good --confidence sure --today 2026-11-20`. Entry: step 1, streak 1, `last_reviewed` 2026-11-20, `next_due` 2026-11-23.

### 6. Pause mid-concept, then return

Data folder: copy of the scenario 1 seed. First half: date 2026-11-16, first message "Can we do a fractions session?". Second half: fresh tutor, same folder, date 2026-11-17, first message "Continue my learning".

Learner script, first half: "3/8. 3 is what I ate, 8 is the slices." / "pause" (sent while the first scored question was waiting for an answer). Second half: "The one cut into 4. Fewer cuts, so each slice is bigger." / "Sure." / "3 from the one cut into 4. Same number of slices, but quarters are bigger than eighths." / "Sure." / explain back / "stop".

| Condition | Result | Evidence |
|---|---|---|
| Resume note written | pass | `sessions.md` after the first half: `### Resume note` with "Concept: top-and-bottom. Step reached: Question ... Last question asked (not yet answered, unscored): two friends, same size pizza, one cut into 4 slices and one into 8 ... Explained directly: no. Confident wrong answer: no." `progress.json` stayed empty. |
| Next session continues that concept | pass | Second-half first turn: "we'll pick up where we left off with top and bottom numbers ... Here is where we stopped. Two friends have pizzas of the same size. One cuts hers into 4 slices and the other cuts hers into 8." |
| Note removed | pass | After the second half, `sessions.md` holds the 2026-11-16 entry without its `### Resume note`, plus a 2026-11-17 entry. Tool log: `start ... top-and-bottom taught --today 2026-11-17`. |

### 7. New learner asks to prepare for AWS Cloud Practitioner

Data folder: empty. Date 2026-11-16. First message: "I want to prepare for the AWS Cloud Practitioner exam". The tutor agent had web access.

Learner script: "Priya" / "Mainly pass the exam. I'm moving into a sales role at a cloud company. I'm an adult, no tech background." / "I've booked it for 2027-01-15." / "30 minutes." / "No, nothing yet." / "Looks good." / a guess ("I guess they could rent the servers instead, so they don't pay so much upfront?" or close to it) / right answers with "Pretty sure" and then "Sure" to two scored questions / explain back ("You don't pay a big amount upfront, you pay for what you use ... you can put them anywhere in the world") / "stop". In the re-runs the tutor's questions differed, so the right answers were reworded to fit them; the learner stayed the same.

Besides the brief's five conditions, three checks were added after review, to cover the design's rule that certification facts come from the documentation: (a) how many documentation pages the tutor fetched at setup and before teaching, from its tool log; (b) every non-null `doc_url` in `path.json` is a page it fetched; (c) every piece of feedback on a scored answer carried a link.

**First run.** The five brief conditions were met: the guide was fetched (WebFetch of `d1.awsstatic.com/.../AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf`), `source` was set with `fetched: 2026-11-16`, weights 24/30/34/12, the Teach turn linked the six-advantages page, and the learner was told "The guide is an outline, not the whole exam". But the run deviated from the design in two ways:

- No documentation pages were read. The tool log has one WebSearch and three WebFetch calls, all for the exam guide, and no service page. All 36 concepts still got a `doc_url`, written without reading the page, for example `managed-services-automation` pointing at the CloudFormation user guide and `integration-other-services` at the SNS page only. Those links happen to resolve, but nobody read them, so they are not evidence that the concepts match the documentation. Fails (a) and (b).
- The feedback on the third scored answer ("You tied the lower price to AWS's costs, which is the economies-of-scale idea") had no link. Fails (c).

Fix round 1 (scenario 7): `subject-setup.md` section 3: read one documentation page per service the guide names, not one per concept, and set `doc_url` only to a fetched page, else `null`, with the reason. `SKILL.md`, Session order: fetch a certification concept's page before teaching it, filling a null `doc_url`. `SKILL.md`, certification paragraph, and teaching-method section 2 (Question): feedback on every scored answer carries the link. `data-files.md`: `doc_url` meaning updated.

Re-run 1 (`s7r1`): brief conditions met. (a) setup fetched 0 documentation pages (guide only); before teaching it fetched the six-advantages page, then the Well-Architected pages for the next concept. (b) pass: 1 of 37 `doc_url` set, to a fetched page; 36 `null`. (c) pass: both scored feedbacks ended "Source: https://docs.aws.amazon.com/whitepapers/latest/aws-overview/six-advantages-of-cloud-computing.html". Still fails the reading at setup: the tutor showed the outline without reading any service page.

Fix round 2: `subject-setup.md` step 4 made the reading a gate: "Read the documentation before you build any concepts ... For a foundational exam that is roughly 20 to 40 pages ... Do not show the outline (section 4) until this reading is done".

Re-run 2 (`s7r2`): brief conditions met. (a) setup fetched 8 exam-guide pages and 22 documentation pages (IAM, EC2, S3 storage classes, VPC, Lambda, RDS, DynamoDB, CloudTrail, CloudWatch, Organizations, support plans, Cost Explorer, Budgets and others); 1 more after the outline. (c) pass: all three feedbacks linked `.../aws-overview/introduction.html`. (b) fails: 27 of 52 concepts have a `doc_url`; 26 were fetched, but `root-user` points at `IAM/latest/UserGuide/id_root-user.html`, while the page fetched was `root-user-tasks.html`.

Fix round 3: `subject-setup.md` step 5: copy each `doc_url` exactly from the address fetched, never from memory, and after writing `path.json` check every non-null `doc_url` against the fetched addresses, setting any mismatch to `null`.

Re-run 3 (`s7r3`), final:

| Condition | Result | Evidence |
|---|---|---|
| Official exam guide fetched | pass | Tool log: WebFetch of 5 pages under `docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/`. Outline: "I've read the official exam guide and about 40 AWS documentation pages". |
| `source.url` and `source.fetched` set | pass | `source: {"url": "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain1.html", "fetched": "2026-11-16"}`. The URL is a page of the guide (domain 1) rather than its index page; it is still the official guide. |
| Domain weights present | pass | `weight_percent` 24, 30, 34, 12. |
| Taught facts carry documentation links | pass | Teach turn: "That is the 'trade fixed expense for variable expense' advantage ([AWS overview: six advantages of cloud computing](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/six-advantages-of-cloud-computing.html))". |
| Told the guide is not the whole exam | pass | "The guide is an outline, not the whole exam, so questions can go into more detail than it lists." |
| (a) Documentation read | pass | 44 documentation pages fetched at setup, before the outline was shown; none needed before teaching, because the first concept's page had been read at setup in this session. The fetch-before-teaching rule was exercised in re-run 1: two concepts' pages fetched and their null `doc_url` filled. |
| (b) Every non-null `doc_url` was fetched | pass | 43 of 55 concepts have a `doc_url`, all 43 among the fetched addresses; 12 are `null`. |
| (c) Every scored feedback carried a link | pass | Feedback 1: "...rather than just naming it ([AWS overview: six advantages](...six-advantages-of-cloud-computing.html))". Feedback 2: "That is the 'economies of scale' advantage ([AWS overview: six advantages](...))". |

Not covered by a condition: the s7r3 tutor sent the learner nothing between the last setup answer and the finished outline, several minutes of reading. Only afterwards did it say it had "read ... about 40 AWS documentation pages". After review, `subject-setup.md` section 3 got a new step 4: write a short message saying what will be read, roughly how many pages and how long, before the first documentation fetch, then start fetching in the same turn. The fix rounds above refer to the earlier step numbers, so their steps 4 and 5 are now steps 5 and 6. This wording change was not re-run, because the test harness cannot show text written before tool calls.

Also seen: `renamed_products` has AWS Single Sign-On to IAM Identity Center, among others. `start ... cloud-value taught` ran (entry `learning`, step 0, due 2026-11-17).

### 8. "How am I doing?"

Data folder: copy of `examples/sample-learner/`. Date 2026-11-16. First message: "How am I doing with fractions?"

`schedule.py summary .../fractions --today 2026-11-16` prints `{"new": 0, "learning": 2, "solid": 1, "retired": 0, "due": 2}`. The path has 6 concepts, 3 with no progress entry.

| Condition | Result | Evidence |
|---|---|---|
| Short text answer with counts matching `summary` | pass | A greeting line, four bullets and a two-line offer to start. Solid: "what a fraction is" (1); Still learning: equivalent fractions, adding fractions (2); "Not started yet: comparing fractions, multiplying fractions and dividing fractions" (3); "Two topics are due for revision now" (2). All match. |
| No page generated | pass | The tutor made 2 Bash calls (`summary`, `due`) and 1 Read, and nothing else: no Write, Edit or Artifact. No new files in the data folder. |

### 9 and 10. Cards and the page

Run together as one session on 2026-11-16, after the eight above, and run differently from them: one tutor agent (Claude Sonnet) played both the tutor and a scripted learner, because the conditions are about files written, not about how the tutor reacts to a surprise. This is weaker evidence than a learner played turn by turn. Data folder: a copy of `examples/sample-learner/`. The session revised the two due concepts, taught `comparing-fractions` with one wrong answer, and ended when the learner said "I have to stop now".

| Condition | Result | Evidence |
|---|---|---|
| 9. One entry for the concept in `cards.md`, in the documented shape | pass | `## 2026-11-16 · comparing-fractions` with The idea, How it shows up and Watch for, one line each, written straight after `start comparing-fractions taught`. `build_page.py` then reported `"cards": 3`. |
| 9. The same card is shown to the learner | pass | The three fields in the conversation match the file word for word. |
| 9. No fact that was not taught or tested | pass | The card restates the slice-size idea and the learner's own 1/4 against 1/8 mistake. |
| 9. A skipped concept has no card | not exercised | No concept was skipped in this session. |
| 10. Asks once about the page and names claude.ai | pass | "Do you want your progress and cards put on a web page? It would be hosted on claude.ai, only this account could see it, and a copy stays on this computer either way." |
| 10. The answer is written to `profile.json` | pass | `"page": "no"`. |
| 10. `page.html` is in the subject folder whatever the answer | pass | Built before the question was asked. |
| 10. With "no", nothing is published | pass | No Artifact call; `page_url` is absent from `path.json`. |

One fault outside the conditions: the tutor twice put a command's arguments in the wrong order and had to retry. `SKILL.md` now shows the order with an example.

## Summary

| # | First run | Final run |
|---|---|---|
| 1 | 3/3 | 3/3 |
| 2 | 4/4 | 4/4 |
| 3 | 2/2 | 2/2 |
| 4 | 3/3 (plus a wrong extra miss entry) | 3/3, re-run after fix round 1 |
| 5 | 2/2 | 2/2 |
| 6 | 3/3 | 3/3 |
| 7 | 5/5 brief conditions, but no documentation read and one feedback without a link | 5/5 plus the 3 added checks, re-run after fix rounds 1 to 3 |
| 8 | 2/2 | 2/2 |
| 9 | 3/3, one condition not exercised | same |
| 10 | 4/4 | same |
