---
type: "[[adr]]"
id: ADR-0027
aliases: ["ADR-0027"]
title: "An acceptance check states its setup, its steps and its expected result, so someone who did not write it can walk it"
status: "proposed"
owner: user:edwin
created: 2026-09-06
updated: "2026-09-06"
source: ["Edwin, 2026-09-06, reading TST-0018 in your-trainer: 'I don't understand the description, in general it might be good to rewrite all the test descriptions because they can be very abstract'", "Measured over your-trainer's 631-check acceptance corpus, 2026-09-06"]
decision: "Option 3 proposed. State the shape in TESTING.md, ship it in the test template so a new check is born in it, and add a grandfathered validator rule for the three mechanical failures. Existing corpora are rewritten on contact, never swept."
context: "A check is written once, by someone holding the whole context, and walked later by someone holding none of it. Nothing in project-os says what a check must contain, so what gets written is a reminder to its author rather than a procedure for its reader."
alternatives: []
consequences: []
supersedes: ""
superseded: ""
related: ["[[ADR-0023-A-Quantified-Rule-Is-A-Decision]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
---

# An acceptance check is walkable by a stranger

## Rule

An acceptance check states, in the note, the setup its walk requires, the steps to take, and the expected result of each — each expressed as something a person can observe without reading source code.

## Domain

Every `[[test]]` at `level: acceptance` in a project-os repo. Not executable tests: a check carrying a `command:` is run by a machine that needs no prose (`ADR-0025`).

## Conformance

**The walker is authoritative.** If someone walking the check cannot tell what to do or what should happen, the check is wrong — not the walker. The discharge is that a check which fails a walk for a *textual* reason gets its text fixed in the same action that records the verdict, and the mechanical half is a validator rule (`## Decision`, option 3).

## Context

The failure is not that checks are badly written. It is that a check is **written by someone holding the whole context and walked by someone holding none of it**, sometimes months later, and nothing in project-os says what has to survive that gap.

Measured over `your-trainer`'s corpus on 2026-09-06 — 631 acceptance checks, the largest in any project-os repo:

| what was measured | count | why it matters |
|---|---|---|
| body under 30 words | 165 | a reminder, not a procedure |
| no expected-result verb anywhere (`verify`, `must`, `expect`, `confirm`) | 160 | says what to do and never what should happen |
| names a code symbol or file with no rider-visible anchor | 71 | the walker has to read source to know what to look at |
| carries a paragraph of migration provenance inside the procedure | 53 | the procedure is buried in bookkeeping about the note |

And three failures that reached a release walk in a single week, each of which the rule would have caught:

- **A check whose premise had expired.** It asked the walker to prove a session outside the sync window is not flagged deleted. The code stopped inferring deletions that way entirely — it now verifies each candidate and acts only on a 404 — so there was nothing left to walk. Nobody noticed until it was walked, because the check never stated what it expected to *see*.
- **A check asserting behaviour the platform never had.** It required an animation to stop in a paused ride; that animation takes no telemetry input and never stopped. Walked as written, it fails for a reason unrelated to any defect.
- **A check that looked expensive and was not.** It asked for hardware to be unplugged mid-test or a known-bad device to be sourced. A developer-settings switch forces the same state in fifteen seconds. It had gone unwalked for months, and the sentence describing the setup is why.

The last one is the general case: **a check is walked as often as its setup sentence makes it look affordable.**

## Options

1. **Prose guidance in `TESTING.md` only.** Cheapest. It is also what the corpus above was written under — nothing said the shape, so nothing had it. Guidance that arrives after the corpus exists changes nothing already written and little of what comes next.

2. **Guidance plus the template.** Ship the shape in `docs/__templates__/test.md` so a new check is born with the headings and an author fills them rather than remembering them. Catches every future check, and nothing else.

3. **Guidance, template, and a grandfathered validator rule.** Add the three mechanical failures to the validator — a check with no expected-result verb, a check whose body is under a floor, a check that says "same as above" or "same setup" without naming what it depends on. Dated like the existing review gate: a warning now, an error after a stated date, so hundreds of existing checks are not a flag-day migration.

## Decision

**Option 3 is proposed.**

The prose alone has been tried in every repo that has an acceptance suite, and the measurement above is the result. The template catches new checks. Only the validator catches the ones a person is about to edit, which is the population that matters — and this project already trusts that pattern, because a rule nobody validates drifts per author until it stops being applied (`ADR-0024`'s own reasoning, and `DECISION-OPTIONS` as the precedent).

**The title first**, because it is the only part most people read. A check's title is a **short claim about what must be true** — seven to ten words, one clause, no "and" joining two claims. It is scanned in a list of hundreds beside its neighbours, so it names the check the way a person would refer to it out loud: *"A purchased PRO is never shown as FREE"*, not *"A paying rider still reads as PRO when Play cannot be reached, and the app waits for Play rather than guessing FREE"*. The second of those was written while drafting this decision, and rejected by the first person who read it — a summary of the note is not a name for it. Everything the title leaves out is what the procedure is for.

**Then the shape**, four headings, which is what would go into `TESTING.md` and the template:

- **Setup** — the state the walk needs, and *the cheapest way to reach it*. If a developer toggle, a mock, or a bundled fixture produces the state, name it. This is the line that decides whether the check ever gets walked.
- **Steps** — numbered, one action each, in the order a person performs them.
- **Expect** — what must be observable, one line per assertion, in the words the surface uses. A code symbol may follow the observable name; it may not replace it.
- **Not this check** — the boundary. What a reader might reasonably think this covers and which check actually covers it.

Provenance — where the check came from, what migration moved it, which audit split it out — goes **below** the procedure under its own heading, or into frontmatter. It is about the note, not about the walk.

**Existing corpora are rewritten on contact, never swept.** A check is brought to this shape when it is walked, invalidated, or otherwise edited. Reason, and it is the important half of this decision: rewriting a large corpus from note text alone manufactures confident assertions nobody verified, which is precisely the second failure listed above. The walk is when a person knows whether the text is true.

## Consequences

- `TESTING.md`, `docs/__templates__/test.md` and `tools/skills/test-authoring/SKILL.md` change together, and they are template-owned, so every consumer repo receives the shape at its next sync. No consumer has to migrate anything.
- The validator rule belongs in `project-os-cockpit` (`validate_docs_bundled.py`), not here — this repo owns the instruction set, that one owns the checks. Accepting this ADR creates work in two repos, which is why the enforcement date is an acceptance thread rather than part of the decision.
- Every existing acceptance check in every repo would warn on day one under option 3. That is the intended reading of "grandfathered": the warning is a worklist, not a regression.
- A check that cannot be written in this shape is usually two checks. That is a finding, not an obstacle.

## Acceptance

- [ ] **The shape is stated once.** `TESTING.md` carries it; the template and the skill link to it rather than restating it (`ADR-0024`).
- [ ] **The enforcement date is chosen**, and the validator rule is filed against `project-os-cockpit` with that date.
- [ ] **Whether the title rule is mechanical.** Word count and a bare "and" are both checkable; whether that is worth a validator rule, or belongs to review, is undecided.
- [ ] **The floor is a number.** "Under a floor" needs a word count that flags reminders without flagging genuinely short checks that are complete. `your-trainer`'s corpus is the sample to pick it against.
