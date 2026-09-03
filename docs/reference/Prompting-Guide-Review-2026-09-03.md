---
type: "[[reference]]"
id: REFERENCE-PROMPTING-GUIDE-REVIEW
aliases: ["Prompting-guide review 2026-09-03"]
title: "project-os against the Claude 5 prompting guides (September 2026): 24 findings with file, line and change"
status: active
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
scope: "project"
source:
  - "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1"
  - "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5"
  - "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5"
  - "Published copy: https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"
related:
  - "[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]"
  - "[[FEAT-0002-Hook-Contracts]]"
  - "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"
  - "tools/instructions/WRITING.md"
---

# project-os against the Claude 5 prompting guides

Reviewed on 2026-09-03 against the template at `~/Dev/repos/project-os`. File and line references are to that repo as of that morning, not to this tracking repo, whose copies of several instruction and skill files differ (a sync is pending).

**The result in one paragraph.** The template's rules mostly point the same way the guides do. What needs work is the delivery: four places still say the opposite of a decision the project already took, the always-loaded instruction files carry history a strong instruction-follower does not need, and the stop-points and delegation nudges are tuned for a model that had to be told to pause.

**What was reviewed.** CLAUDE.md, AGENTS.md, CONTEXT.md, LLM_BRIEF.md, the 17 instruction files, the 25 skills, the 4 adapters, the 8 Claude Code hooks, the 2 generated subagents, the 18 note templates, and the adapter generator. Not reviewed: the validator internals, the cockpit, and this repo's diverged copies.

**How to read the labels.** *Fix* means two instructions disagree and the model will obey whichever it read last. *Tighten* means the instruction works but costs more than it needs to. *Add* means the guide covers a behaviour project-os is silent on. Tally: 4 to fix, 12 to tighten, 7 to add, 6 already aligned.

## 1. Instructions that contradict each other

The Fable 5 guide's headline is that instruction-following is now strong enough to steer with a sentence. The flip side is that a contradictory sentence is obeyed too. These four are places where the project decided something and the old wording survived.

### 1.1 Four statements still require a different model family for review (Fix)

**Guide.** Fable 5: fresh-context verifier subagents outperform self-critique. Opus 5: do not spend subagents double-checking your own work. Both point at context, not model family, as what a reviewer needs.

**Today.** ADR-0013 already says exactly that, and QUALITY.md and rule 1 of the review skill state it. But four other places still instruct the old rule, so an agent reading the skill's checklist is told to find a different model two paragraphs after being told it need not: `tools/skills/independent-review/SKILL.md:45` ("Launch the review with a different model"), `tools/skills/docs-audit/SKILL.md:46` ("a fresh model family"), `tools/adapters/claude-code/ADAPTER.md:158` ("require a different model family or a human"), `tools/instructions/HOOKS.md:92` (HC-008's rule line: "must not be performed by the authoring model").

**Change.** Rewrite all four to the ADR-0013 rule: a clean context that is not the authoring session. Rename HC-008 from "model routing hint" to "delegation hint", since the model is no longer what it routes. The generated reviewer prompt already has the right wording.

### 1.2 Grandfathering is described two incompatible ways (Fix)

**Guide.** Fable 5: the model performs better when it understands the reason. A reason that contradicts another reason cancels both.

**Today.** `tools/instructions/QUALITY.md:43` says the feature-requirement gate is keyed on the note's `updated:` date and re-arms when a grandfathered note is edited for any reason. `tools/instructions/STATUSES.md:42` says there is no date-based exemption, grandfathered items are listed by ID, and the date heuristic was removed because of that very re-arming (ISS-0007).

**Change.** Delete the QUALITY.md paragraph and link to STATUSES.md "Grandfathering". STATUSES.md already claims to be the single source for gates; this is the one restatement left.

### 1.3 Release skills and two templates use vocabulary the taxonomy retired (Fix)

**Guide.** Fable 5, "Refactor existing prompts and skills": skills written for earlier models are often stale as well as over-prescriptive, and a strong instruction-follower will write the stale value.

**Today.** The release skills predate ADR-0008, ADR-0031 and ADR-0034 and were not swept. An agent running release-prep will look for `CHK-*` files that no repo has, count "Tier 1 and Tier 2" in a system that says it has no tiers, and write `staged` and `rolled-back`, which the release status list does not contain.

| Where | Says | Current rule |
|---|---|---|
| `release-prep/SKILL.md:21,37`, `release-verification/SKILL.md:67` | `docs/tests/acceptance/CHK-*.md` | Acceptance checks are `TST-*` at `level: acceptance` (TESTING.md:129) |
| `release-prep/SKILL.md:38,41,84,94`, `release-verification/SKILL.md:68,73`, `__templates__/release.md:49-52,72` | Tier 1 / 2 / 3 | "There is no tier system" (TESTING.md:13); sections derive from `covers:` and `command:` |
| `__templates__/SCHEMAS.md:221` | `tier` is a required field | Same contradiction, in the schema itself |
| `release-prep/SKILL.md:50-51`, `feature-scaffold/SKILL.md:52` | `in-review`, `in-progress` | Feature statuses are `review` and `doing` |
| `release-prep/SKILL.md:91`, `release-verification/SKILL.md:104` | `staged` in the release flow | Removed by ADR-0008; the same file says so one line later |
| `release-verification/SKILL.md:126,128` | `rolled-back` | Release statuses are `draft`, `released`, `reverted` |
| `release-verification/SKILL.md:84-85`, `TAXONOMY.md:55` | `kind: manual` / `automated` | `kind` was removed (SCHEMAS.md:194); `command:` decides |
| `__templates__/README.md:21-22`, `__templates__/acceptance-tests.md:17` | "Includes `check.md`", `type: [[check]]` | There is no check.md in the directory and no check type (SCHEMAS.md:227) |

**Change.** One sweep: rewrite release-prep and release-verification against STATUSES.md and TESTING.md as they stand, drop `tier` from the schema and template, remove the check.md lines from the templates README, and move the `kind` heading in TAXONOMY.md to the retired list. This is the docs-audit skill's own "instruction/template drift" dimension; running it here would have caught all eight rows.

### 1.4 The adapter says the subagent pins are the strongest available model (Fix)

**Guide.** Fable 5.1: at `low` effort it is often competitive with Opus and Sonnet on cost per task while scoring higher; re-run the effort sweep per model. Opus 5: review accuracy holds at lower effort.

**Today.** `tools/scripts/generate-adapters.py:60-61` pins both subagents to `claude-opus-5` and `tools/adapters/claude-code/ADAPTER.md:156` explains the choice as "the strongest available Claude model". That was true when written and is not now. The session model in `.claude/settings.json` is `opus`.

**Change.** Either retarget the pins to Fable 5.1 or change the adapter's sentence to describe the pins as a deliberate choice revisited per model release, with a pointer to the effort guidance. Note in ADAPTER.md that the reviewer does not need the highest effort the harness allows.

## 2. Stop-points and finishing the task

Both Fable guides carry the same instruction: pause for the user only for a destructive action, a real scope change, or input only they can provide, and when you do pause, deliver everything that does not depend on the answer first. project-os has eleven stop-points, each worded on its own.

### 2.1 State the pause rule once and make the eleven stop-points defer to it (Tighten)

**Guide.** Fable 5, "Strong instruction following": "Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise."

**Today.** Most of the eleven are legitimate scope changes (an impact conflict, a task ahead of its phase, release scope) or human-only input (a manual test verdict). But each is phrased as a full stop with nothing about what to finish first, and the wording differs everywhere: "stop and present resolution options", "warn and require explicit user confirmation", "stop and request explicit user confirmation", "Present the list to the user for decision". Locations: `LIFECYCLE.md:61`, `HOOKS.md:56`, `status-transition/SKILL.md:28`, `issue-intake/SKILL.md:25,53`, `feature-scaffold/SKILL.md:50`, `release-prep/SKILL.md:34`, `close-out/SKILL.md` step 1, `.claude/agents/planner.md:13`.

**Change.** Add the guide's sentence to LIFECYCLE.md under "Execution", followed by one line from Fable 5.1: "First do everything that does not depend on the answer; then put the question at the end of a turn that also delivers that progress." Then shorten each stop-point to name the decision the user owns and link to that rule. Close-out step 1 gets the guide's blocked-part sentence: complete every other part in full and say exactly what was left out and why.

### 2.2 The Stop hook tells the model to "acknowledge to continue" (Tighten)

**Guide.** Fable 5.1, "Finish the whole task": before ending the turn, check the last paragraph; if it is a promise about work not done, do the work; end only when complete or blocked on the user.

**Today.** When focus is still set, `tools/adapters/claude-code/hooks/close-out-check.sh:52,62` blocks the stop with "If work is ongoing, this is expected — acknowledge to continue." The model receives a block and an instruction that is not an action. It will either write a sentence of acknowledgement (a wasted turn) or resume work it had decided to hand off.

**Change.** Make the reason name the two real actions: "If the work is complete, set the status and clear focus now. If you are stopping mid-flight for the user, write the handoff (HANDOFF.md, 'Before stopping work') in the task note, then stop." The loop guard already lets the second stop through.

### 2.3 The spec-ambiguity check has no threshold, and the planner returns nothing on ambiguity (Tighten)

**Guide.** Fable 5.1, "Delivering work": make routine judgment calls yourself; check in only when different readings would lead to materially different work; otherwise implement the reading the wording most directly supports and state the assumption. The guide warns the autonomy block can make the model ask less about ambiguous requests, so a deliberate counterweight is right. It just needs the threshold.

**Today.** `tools/skills/issue-intake/SKILL.md:25` lists five tests and says "if any fails, ask the user (or record the open question and set triage) instead of guessing." A term with two meanings in the codebase fails test one even when both readings lead to the same fix. The planner subagent (`.claude/agents/planner.md:13`, generated from `generate-adapters.py:75`) goes further: on ambiguity it returns questions and allocates nothing, so a five-part scaffold with one unclear item yields zero notes.

**Change.** Add the guide's threshold sentence to the check and make "record the assumption in the note and proceed" the default, with the question-plus-triage path reserved for readings that diverge materially. Change the planner's rule 5 to "allocate and draft what is settled; return the ambiguities as questions beside it."

### 2.4 The document-first gate blocks files outside any project-os repo (Tighten)

**Guide.** Fable 5.1, "Finish the whole task": a blocked step the model cannot resolve ends the turn or forces a workaround. A gate should block only what its rule covers.

**Today.** Writing this review to the session scratchpad was denied with "No active task or issue in SNAPSHOT.yaml focus." The hook walks up from the target path looking for a snapshot, finds none, then falls back to the session repo's snapshot, whose focus is empty (`tools/adapters/claude-code/hooks/document-first-gate.sh:43`). A scratch file is not code in a project-os repo, and the workaround (write through the shell) is exactly the bypass the hook exists to prevent.

**Change.** Already on record as point 3 of [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]], updated the same day with the four-path reproduction and the corrected fix: fall back to the session repo only for a relative path or a path inside it; allow anything else.

## 3. Delegation

### 3.1 The per-prompt hint pushes delegation for work that is a handful of tool calls (Tighten)

**Guide.** Opus 5, "Controlling subagent spawning": "Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several." Fable 5 and 5.1 add: give explicit guidance about when delegation is appropriate, and let the lead keep working while a subagent runs.

**Today.** HC-008 (`tools/adapters/claude-code/hooks/model-routing-hint.sh:57-75`) fires on every prompt. In every terminal or empty state it says "delegate preflight to the 'planner' subagent before coding", and every variant ends with "Independent review goes to 'independent-reviewer'." Preflight for a one-line bug fix is one issue note and one snapshot entry; a planner subagent re-reads the repo to produce them. The review sentence appears on prompts that are questions.

**Change.** Have the hint serve the focus state (item, status, phase) rather than instruct, which is what [[FEAT-0021-Serve-Orientation-Answer-Lookup]] already plans. Recommend the planner only for multi-item scaffolds or an ambiguous ask; say the main loop does preflight for a single issue or task. Emit the review sentence only in review states. Add one line so the lead investigates the code while the planner runs instead of waiting; HC-001 blocks edits, not reading. The documentation requirement itself does not change: every change still gets its note before code.

### 3.2 The planner is handed the request without the reason (Add)

**Guide.** Fable 5, "Give the reason, not only the request": the model connects the task to relevant information when it knows what the output is for.

**Today.** The planner prompt (`tools/scripts/generate-adapters.py:63-78`) says what to produce and how, but nothing tells the lead to pass along the user's own words and why the work is wanted. The lead paraphrases, and the planner classifies the paraphrase.

**Change.** Add to the hint and to the planner prompt: the delegation carries the user's prompt verbatim and one sentence on what the result enables. The issue template's "Problem" section is where the verbatim text lands (see 7.3).

## 4. Instruction weight and prose

Fable 5's scaffolding advice is blunt: skills developed for prior models are often too prescriptive and can degrade output; review and remove what default behaviour now covers. project-os's rules are mostly still needed. Its histories are not needed in the files an agent loads every session.

### 4.1 Normative files carry the war stories, not just the rule and its reason (Tighten)

**Guide.** Fable 5: a brief instruction with its reason steers as well as an enumeration. Fable 5.1: denser prose with fewer breaks is the model's own failure mode, and a prompt written that way teaches it. The instruction README agrees with both: "Use a short title and explicit Rules bullets; avoid narrative prose where possible" (`tools/instructions/README.md:17`).

**Today.** The files break the README's rule, and the cost lands where it is most expensive.

| File | Words | Loaded | Example of what could move to the ADR |
|---|---|---|---|
| STATUSES.md | 2,772 | Cursor: always; Claude: on demand | The retired `[[check]]` section; the ISS-0006 story in the preamble |
| TESTING.md | 1,608 | on demand | "54 rows carried a hand-written RE-RUN annotation and all 54 were still ticked" |
| QUALITY.md | 1,408 | Cursor: always | The italic ISS-0196 paragraph on how the gate used to be read |
| DECISIONS.md | 1,381 | on demand | Census dates and the DECISION-RULE landing narrative |
| LIFECYCLE.md | 1,343 | Claude and Cursor: every session | "A local pass is not a CI pass": two anecdotes under a rule that is two lines |
| Cursor always-on rules | 5,711 | every session | The four files above, inlined |

None of the reasons should go. The pattern the guide endorses is rule, one-line reason, link. The stories already live in ADRs and change notes; the instruction files repeat them.

**Change.** Pass over the six files with a fixed shape per rule: the normative sentence, one sentence of why, and the ADR or ISS reference. Move the anecdotes to the ADR's Context section where they are missing. Target: LIFECYCLE.md under 800 words, since it is the file every Claude Code session loads.

### 4.2 The instructions use the mannered prose the writing guide warns about (Tighten)

**Guide.** Fable 5.1, "Writing density": "Mannered prose substitutes metaphor and flourish for direct statement. Instead of 'a parameter worth varying,' the mannered writer produces 'a dial worth turning.' The fix is to say what you mean. When a literal phrase is available, use it."

**Today.** The 2026-08-31 feedback was about exactly this, and WRITING.md answers it well. But the instruction corpus the model reads before writing is full of the pattern, so the model learns it from the prompt: "the load-bearing sentence" (`STATUSES.md:151`), "a badge that never empties" (`TESTING.md:678`), "a one-way door" (`TESTING.md:604`), "the drift travelling under its own fix" (`TAXONOMY.md:427`), "decided by whoever was tired" (`feature-scaffold/SKILL.md:61`), and in WRITING.md itself, "two sentences wearing one hat" (`WRITING.md:25`).

**Change.** Add the guide's mannered-prose definition to WRITING.md as rule 7, then apply it during the 4.1 pass.

### 4.3 Template frontmatter comments restate rules every scaffolded note then carries (Tighten)

**Guide.** Fable 5: a short instruction is as effective as the enumeration. Opus 5: files the model writes to disk run long; calibrate.

**Today.** `docs/__templates__/feature.md:15-22` carries an eight-line comment explaining `acceptance_exception`; `docs/__templates__/test.md:26-33` carries nine lines of comments on the acceptance fields and ADR-0037. Every scaffolded feature and test inherits them unless the agent deletes them, and most do not.

**Change.** One line per field plus a pointer to SCHEMAS.md, which already holds the full explanation.

### 4.4 Every generated skill repeats three close-out steps and says "exactly" (Tighten)

**Guide.** Fable 5: skills for prior models are often too prescriptive; the model updates skills on the fly from what it learns. Opus 5: explicit verification instructions cause over-verification.

**Today.** All 25 generated `.claude/skills/*/SKILL.md` bodies (`tools/scripts/generate-adapters.py:140-148`) end with "run validate-docs", "run --as-committed before pushing", and "confirm the run went green", including inbox-triage and ad-hoc-intake, which push nothing. Step 2 says "Execute its checklist exactly."

**Change.** Generated body: the pointer to the canonical playbook and its "when to use" bullets. The three close-out lines stay in the close-out skill only. Replace "exactly" with "follow its checklist; where the checklist and the repo disagree, say so and file an ISS-* rather than improvising."

## 5. Writing for the reader

### 5.1 WRITING.md matches the guides; four sentences would complete it (Add)

**Guide.** Fable 5, "Readability when communicating with the user": the final message after a long run is the reader's first look; write it as a re-grounding, drop working shorthand, arrow chains, hyphen-stacked compounds and labels made up while working. Fable 5.1: before starting, say in a line what you are about to do; close with a recap that stands alone. Both: keep output short by being selective, not by compressing.

**Today.** WRITING.md's thesis ("the failure mode is compression, not length") is the guide's, and rules 1 to 6 cover point-first, one idea per sentence, concrete subjects, glossed terms. Missing: the between-tool-calls versus final-message distinction, the ban on arrow chains and invented labels, the selectivity rule, and any cadence guidance. `AGENTS.md:50-51` asks instead for a fixed-format preamble ("purpose, active feature/task/issue, intended files"), which produces a report nobody reads.

**Change.** Add rules 7 to 10 to WRITING.md: the re-grounding paragraph, "no arrow chains or made-up labels", "drop details that do not change what the reader does next", and the one-line-before / standalone-recap cadence. Replace AGENTS.md "Output expectations" with a link to those rules.

### 5.2 Notes and snapshot fields have no length calibration, and it shows (Add)

**Guide.** Opus 5, "Written deliverable length": "Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate."

**Today.** `tools/instructions/SNAPSHOT.md:63` defines `title` as "Short human title (no ID)" and `goal` as a short outcome statement. In the template's own snapshot, `focus.note` is 266 words; in this repo it is 136. FEAT-0021's title is a 30-word sentence. The narrative is real and useful; the field is the wrong container, because the snapshot is what every session loads first.

**Change.** SNAPSHOT.md: title at most twelve words; `goal` and `note` at most two sentences; anything longer goes in the note body under "Next Actions". Templates: "Summary: two or three sentences, point first" on change.md, issue.md Problem, and feature.md Goal.

### 5.3 Grounded claims: extend the evidence rule from notes to chat (Add)

**Guide.** Fable 5, "Ground progress claims during long runs": "Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that."

**Today.** project-os enforces this for notes: criteria ticked only with an evidence pointer, "not landed until you have seen CI green", tests that carry adequacy evidence. Nothing says the same about the final message (`tools/instructions/QUALITY.md:56`, "Verification expectations").

**Change.** Add the guide's sentence to that section.

## 6. Scope

### 6.1 Nothing says what to do with a bug you notice but were not asked to fix (Add)

**Guide.** Fable 5.1, "Keep changes and tests to what the task asks for": a pre-existing bug or unmentioned behaviour is a follow-up in the summary, not a change in this diff; with the instruction, unrequested additions drop substantially with no change in task success. Fable 5: no surrounding cleanup on a bug fix, no abstractions for hypothetical requirements.

**Today.** project-os has the perfect sink for this and does not name it. Every rule is about documenting what you change; none is about not changing what you noticed. The document-first gate would even block the extra edit if it had no focus item, and an agent routes around that by widening the current task.

**Change.** LIFECYCLE.md "Execution": "Something you notice that the task did not ask for, whether a bug, a cleanup or a missing abstraction, is an ISS-* at triage or a follow-up in your summary, not a change in this diff, unless the requested behaviour cannot work without it." Add the guide's ambiguity sentence: implement the reading the wording most supports and state the assumption in the task note.

### 6.2 Tests sized to the task, and scratch checks not kept (Add)

**Guide.** Fable 5.1: commit tests only where the task asks or the repo already keeps tests for this kind of change, sized like the neighbouring test files, roughly one focused test per stated behaviour; do not turn scratch checks into permanent test files.

**Today.** `feature-scaffold/SKILL.md:59` mandates one acceptance check per feature (a rule with measured backing) and test-authoring covers the note. Neither says anything about code tests or scratch scripts, and the verification gate rewards linking more TST notes.

**Change.** One paragraph in test-authoring: a TST-* note is the record of verification; scratch checks used to reach it are not kept; committed code tests follow the repo's convention and are sized to the stated behaviours.

## 7. Handoff, edits, quoting, batching

### 7.1 HANDOFF.md preserves state but not the roads not taken (Add)

**Guide.** Fable 5.1, "Tell the model what to preserve in compaction summaries": approaches raised, tried or set aside and why; anything decided, ruled out or established as a constraint, stated exactly; details hard to reconstruct.

**Today.** `tools/instructions/HANDOFF.md:17-22` has four items: statuses, focus, what was done and what is next, and uncommitted work. A successor gets the position but not why the other paths were closed, so it re-explores them.

**Change.** Add two items to "Before stopping work": approaches tried and set aside, with the reason; and constraints or user decisions in their exact words. Both belong in the task note's "Next Actions" section.

### 7.2 Edit the lines that change; do not rewrite a note (Add)

**Guide.** Fable 5.1, "Prefer targeted edits over whole-file rewrites": a one-line instruction restores targeted edits.

**Today.** `tools/instructions/MARKDOWN.md:19` says not to reflow existing prose for wrapping, but nothing says a small change to a note is an edit rather than a rewrite. Rewriting a note is how review fields, waivers and `origin:` get dropped, and it bumps `updated:` on prose that did not change.

**Change.** One rule in MARKDOWN.md: "Change the lines that change. Rewriting a note to make a small edit loses frontmatter you did not mean to touch."

### 7.3 Verbatim prompts in notes should read as quotations (Add)

**Guide.** Fable 5.1, "Quoting retrieved sources": the record should distinguish quoted words from the agent's own.

**Today.** `tools/skills/ad-hoc-intake/SKILL.md:36` says "capture the prompt verbatim in the note (Problem/Evidence)", with no format, so the user's words and the agent's paraphrase sit in the same paragraph. DECISIONS.md already solved this for human decisions with a callout "in the decider's own words".

**Change.** Issue template: a blockquote under Problem labelled "As reported", and the intake skills say to put the verbatim text there.

### 7.4 Numbered checklists read as sequences (Tighten)

**Guide.** Fable 5.1, "Batch independent tool calls": in coding loops the model may issue one call per turn when the next steps are implied rather than requested.

**Today.** Every skill is a numbered checklist (`tools/skills/README.md:16-21`), and many steps are independent. Numbering says "in this order".

**Change.** One sentence in the skills README: numbers are for reference; do the steps that do not depend on each other in one go.

## 8. Reviewer output

### 8.1 Filtering findings at the reviewer suppresses them (Tighten)

**Guide.** Opus 5, "Code review and bug-finding": "If your review prompt says 'only report high-severity issues' or 'be conservative,' the model may follow that instruction literally and report less; ask it to report everything and filter in a separate pass instead."

**Today.** `tools/skills/independent-review/SKILL.md:47-50` asks the reviewer to refute, which is right. This repo's `tools/scripts/review-external.py` then enforces "a finding without a repro is not a finding" in the reviewer's output schema, so the reviewer drops the plausible-but-unreproduced ones itself.

**Change.** Ask the reviewer for everything, each finding labelled reproduced or not. Apply the repro filter when transcribing findings to ISS-* notes, which is a separate pass by construction.

## 9. Already aligned

- **Reasons everywhere.** Fable 5's "give the reason" is the house style. Finding 4.1 is about volume, not the principle.
- **No show-your-thinking instructions.** The Fable 5 audit item on reasoning extraction finds nothing; the reviewer is told never to see the author's reasoning.
- **Fresh-context reviewer.** ADR-0013 and the generated reviewer prompt are the guide's "fresh-context verifier subagents outperform self-critique", stated more carefully than the guide does. (Corrected 2026-09-03: the sentence is in the Fable 5.1 migration guide's long-running-agent recommendations, "separate fresh-context verifier sub-agents tend to outperform self-critique", not only in the Fable 5 guide. The Opus 5 guide says the opposite, "do not use subagents to review, verify or double-check your work"; the two guides disagree on this point.)
- **Evidence before status.** Ticked-with-evidence criteria, tests that must fail when the fix is broken, "not landed until CI is green".
- **Docs audit to quiescence.** Two clean passes before convergence is the guide's periodic self-verification with a stopping rule.
- **Inbox triage on images.** "Do not paraphrase an image into a note and throw the image away" matches the vision guidance.

## 10. Guide items with no project-os surface

Harness or API concerns the guides raise that project-os correctly leaves to the tool: effort parameters, the thinking display setting, append-only conversation history, turn-scoped system messages, a send-to-user tool, client-side compaction, and the max-tokens note for long outputs. Two footnotes: safeguard false positives can fire on base64 in tool output, and design artifacts embed base64 assets, so a cockpit or reviewer that reads an artifact back could strip data URIs first; and the hint hook already behaves like a turn-scoped reminder, which is the shape the 5.1 guide recommends.

## Suggested order

1. The contradictions (1.1 to 1.4). Cheap, mechanical, and each is currently steering an agent wrong.
2. The one-sentence rules (2.1, 5.3, 6.1, 7.1, 7.2, 7.4): a dozen lines across LIFECYCLE.md, QUALITY.md, HANDOFF.md, MARKDOWN.md and the skills README.
3. WRITING.md (4.2, 5.1) and the length calibration (5.2), since they change what every note and reply looks like.
4. The trim (4.1, 4.3, 4.4) as one feature with a word-count target, and the hook and hint rewrites (2.2, 2.4, 3.1, 3.2) alongside FEAT-0021.

Planning of these findings into issues, features and tasks in this repo was started on 2026-09-03; the resulting items link back here.
