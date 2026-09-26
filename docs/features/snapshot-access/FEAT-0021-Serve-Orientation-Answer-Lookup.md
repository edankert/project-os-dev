---
type: "[[feature]]"
id: FEAT-0021
aliases: ["FEAT-0021"]
title: "Serve orientation, answer lookup: the startup hook emits the in-flight slice instead of a reminder, and a format-independent query replaces grep against YAML"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-08-03
updated: 2026-09-25
source: ["fleet measurement 2026-08-03: 590 sessions", "user decision 2026-08-03", "ISS-0031"]
goal: "Stop instructing agents to read the snapshot and start giving them what reading it was for. Orientation is served by the SessionStart hook at 513–3,418 tokens in five of six repos; lookup gets a query interface, because grep against YAML returns different information depending on which of the fleet's two styles a repo uses."
requirements: []
tasks: ["[[TASK-0080]]", "[[TASK-0081]]"]
release: ""
related: ["[[ISS-0031]]", "[[ISS-0030]]", "[[ADR-0017]]", "[[ADR-0002]]"]
tests: ["[[TST-0007]]", "[[TST-0024]]"]
acceptance_exception: "Hooks and scripts with no screen of their own. They are checked by TST-0007 and TST-0024, by a headless session that quoted the orientation from its context (2026-09-24), and by a comparison with PyYAML over every fleet snapshot (2026-09-25)."
reviewed_by: ["model:claude-opus-5-5", "model:claude-opus-5-5", "model:claude-opus-5-5"]
review_date: 2026-09-25
review_round: 2
review_verdict: approved
---

# Serve orientation, answer lookup

## Goal

[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs|ISS-0031]] established that one prescribed method — *"Read SNAPSHOT.yaml at session start"* — covers two needs it cannot both serve, and that agents take the instructed action in **5 of 260 accesses**. This feature addresses each need with the mechanism that fits it, rather than restating the instruction more firmly.

- **Orientation** is *served*, by the hook that already fires.
- **Lookup** is *answered*, by a query that does not depend on the file's YAML style.

## Why not simply add a tool and instruct agents to run it

Because that solves a compliance problem by adding a second instruction whose compliance nobody has measured. The measured uptake of the existing startup instruction is ~2%. A `pos brief` that agents must be told to run inherits exactly that number.

[[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] clause 1 is the applicable principle one level up: where something can be derived and delivered, deliver it rather than asking a party to do it and hoping. The `SessionStart` hook already fires, already emits text into context, and currently spends that budget on a *reminder to read the file*. Spending it on the file's orientation-bearing content instead removes the compliance question rather than relocating it — the agent does nothing, so there is nothing to comply with.

## Measured basis

**The orientation slice is affordable** — focus, counts, and in-flight items only (`doing`/`review`/`open`/`triage`), with fields trimmed to title/status/file/parent/phase:

| repo | full file | in-flight slice | items |
|---|---:|---:|---:|
| project-os-cockpit | 49,992 | **513** | 4 |
| your-applications.com | 38,466 | **778** | 11 |
| your-sudoku | 14,617 | **1,294** | 16 |
| project-os-dev | 15,881 | **1,663** | 18 |
| your-health | 46,396 | **3,418** | 67 |
| your-trainer | 96,636 | **11,573** | 58 |

**Grep is format-dependent, and both formats are in the fleet.** The same query returns different information depending on a repo's YAML style:

| repo | style | `grep "TASK-XXXX:"` returns |
|---|---|---|
| your-trainer | inline flow-map | 879 bytes — **includes `status`** |
| project-os-dev | block | 15 bytes — the ID alone; the next line is `file:`, **not `status`** |

An agent asking for an item's status gets it in one repo and silently does not in another. That is a correctness defect in the dominant access path (255 of 260 accesses), not an ergonomic complaint, and it is the load-bearing argument for TASK-0081.

## Scope

- **TASK-0080** — the `SessionStart` hook emits the in-flight slice. Changes hook contract **HC-002**, whose current rule is a reminder ("Implementations: Claude Code `hooks/snapshot-freshness.sh` (SessionStart reminder); Codex/generic `bash tools/agents/bootstrap.sh`").
- **TASK-0081** — a format-independent query for lookup, with stable output.

## Out of scope

- **Pruning** ([[ISS-0030-Retention-Is-Policy-Nothing-Performs|ISS-0030]]). Independent and complementary: this feature makes the file's *size* matter less by never requiring a whole-file read, which weakens the token argument for retention while leaving the retrieval-quality argument intact.
- **Write operations.** A `pos task create` interface is a larger idea from the 2026-07-29 comparable-systems review; this feature is read-only, and adding writes would put note authoring behind a tool that ADR-0009 deliberately keeps in the notes.

## Known complications

**`your-trainer`'s slice is 11,573 tokens for 58 items, while `your-health` fits 67 items in 3,418.** The difference is title length — `ISS-0359`'s title is a paragraph of crash-report forensics. So either the emitter truncates titles at a fixed width, or that repo has a title-as-abstract problem distinct from its retention one. Decide before building; a hook that injects 11.5k tokens into every session in one repo has re-created the cost this whole line of work was checking for.

**HC-002 is a tool-agnostic contract with per-tool implementations** ([[ADR-0002]]). Changing it means the contract, the Claude Code hook, and the Codex/generic `bootstrap.sh` move together, and the change propagates to twelve repos via `sync-project-os.sh`.

**The query tool inherits the discovery problem.** Agents reach for grep without being told; they will not reach for a project-specific command unless something puts it in front of them. The one surface that reliably reaches them is the hook output — which this feature is already changing, and which can therefore advertise the query at the point of use. That coupling is the reason to build both halves together rather than separately.

## The honest counter-case

[[ISS-0031]] option 4 — *do nothing until measured* — remains defensible for the orientation half. `project-os-bench` TASK-0008 with a grep-only arm would establish whether grep-only orientation is actually worse before anything is built.

The two halves differ on this. **TASK-0081 does not need the measurement**: format-dependent lookup is a defect on its own evidence. **TASK-0080 is sound on ADR-0017's principle but unquantified in value** — serving beats instructing regardless, yet how much it buys is exactly what TASK-0008 would measure. Sequencing TASK-0081 first, and letting TASK-0080 wait on the bench result, is a legitimate reading of this feature and should be revisited at planning rather than settled here.

## Acceptance

- [x] A session in any fleet repo begins with focus, counts and in-flight work already in context, without the agent reading `SNAPSHOT.yaml` — evidence: TASK-0080; a headless session in this repo quoted the orientation from its context on 2026-09-24. Every repo that takes the template gets it; the others do at their next sync.
- [x] The emitted slice stays within a stated token budget in every repo, including the worst case, or the emitter truncates to hold it — 6,000 characters; your-trainer, the largest, 5,945 on 2026-09-25 after the review fixes; TST-0007 asserts 400 items stay under it.
- [x] An item's status can be retrieved by one command that returns the same shape regardless of the repo's YAML style — `snapshot-query.py`, TASK-0081; TST-0024 asserts identical output in both styles.
- [x] HC-002, its implementations and the startup instruction surface agree, with the rule stated once rather than restated per adapter — HC-002 states it; the Claude Code hook, the Codex hook and `bootstrap.sh` call one script; AGENTS.md, CLAUDE.md and HANDOFF.md point at the orientation instead of restating it.

## Verification

2026-09-25, template working tree: every `tools/scripts/test-*.sh` and `test-*.py` passes, among them `test-snapshot-query.sh` 12 of 12 (TST-0024) and `test-hooks.sh` 102 of 102 (TST-0007); `validate-docs.sh` OK; `generate-adapters.py --check` 65 current. In this repo, `run-tests.py`: 24 test notes passing, 0 failing.

## Review

**Round 1, 2026-09-25. Verdict: `changes-requested`.** Two `independent-reviewer` subagents on one packet, each in a clean context and each breaking guards in its own copy (ISS-0085). Both found the same main defect.

| Claim | Combined verdict | Evidence, and what was done |
|---|---|---|
| Criterion 3 and author claims 1 and 3: one command answers the same way in both styles, and an absent id comes from its note | **refuted for change notes** | Both: a `CHG-` id carries a slug, and the parser and the query cut it to `CHG-YYYYMMDD`. Asked for `CHG-20260721-Requirement-Lifecycle-Closure`, the query said "not in SNAPSHOT.yaml" and printed a different note from the same date, exit 0. **Fixed:** an item key keeps a change's slug (and a letter after its date, `CHG-20260531e-...`); a date alone is answered when one change has it and reported as ambiguous, with the candidates, when several do. Compared against PyYAML over all 13 fleet snapshots afterwards: 3,290 items, 269 of them changes, 0 mismatches. |
| Criterion 4: the startup surface agrees, rule stated once | **refuted for lookup** | Both: `AGENTS.md` step 3 still said "Open the whole file only to look something up". **Fixed:** it names `snapshot-query.py`. |
| Author claim 2: the orientation keeps its content and cap | cap holds; content changed (A) | The longer closing line pushed one item in your-trainer into the "more" count. **Fixed:** the line is shorter, and names the query only where the script exists (B's observation 4); your-trainer is back to "and 25 more" at 5,945 characters. |
| Criteria 1 and 2, TST-0007, TST-0024 | holds | Both reviewers broke the truncation, block-list and note-fallback guards in their copies and saw tests fail. |

**Other observations, and what was done:** a block list written at its key's own indent was dropped in block style (B): read now. A quoted comma split an inline list (B): lists split at top-level commas only. Inline maps gave lists as strings (B): lists now. An empty block value became `[]` (A): it stays `""` until a list item appears. Ids with a filter silently dropped the filter (A): a usage error now. `--in-flight` claimed to match the orientation (both): the usage text now says focus items are included. `test-hooks.sh` runs 79 of 102 assertions in a copy without `.git` (both): recorded on ISS-0085, since it affects every mutation run in a copy.

Each fix has a test that fails when it is undone: `test-snapshot-query.sh` grew from 12 to 22 assertions, and six mutations each failed it (recorded on TST-0024). Round two goes to one reviewer.

**Round 2, 2026-09-25. Verdict: `approved`.** One reviewer, clean context, mutations in its own copy. Every refuted claim is *fixed*: it queried every change id in three repos (project-os-dev 9 of 9, your-applications.com 56 of 56, project-os-cockpit 103 of 103), with identical answers after re-dumping each snapshot to block style; a date alone was ambiguous or answered as it should be; `AGENTS.md` names the query; your-trainer's orientation is back to "and 25 more"; each listed fix held; two of the six mutations, re-run, failed their tests.

It also bounded the author's evidence: "0 mismatches" covered the fields a lookup returns, not every field, and in about 30 long quoted prose fields `scalar()` kept `\"` as written. `scalar()` is code this feature brought in (TASK-0080), so it was fixed before close: double-quoted escapes, including `\u2019` and its kin, and single-quoted `''` are now read as YAML reads them. Compared against PyYAML afterwards, every scalar and list field of every item in the 13 fleet snapshots: 20,225 fields, 0 mismatches. A new assertion in `test-snapshot-query.sh` fails when escapes are kept as written (23 of 23 pristine).

The one key the parser and PyYAML disagree on, project-os-cockpit's `REL-0001`, is the cockpit's own defect: its `SNAPSHOT.yaml` declares `items.releases` twice (lines 1834 and 4559), and PyYAML keeps only the second, empty one. The parser keeps both. Reported to Edwin rather than fixed, since another session is working in that repo.
