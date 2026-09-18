---
type: "[[adr]]"
id: ADR-0047
aliases: ["ADR-0047"]
title: "A finding is fixed in the feature that caused it, and a review is sized to the change"
status: proposed
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18, on review effort and on issues 'not fixed as part of the features they belong to'"]
decision: "Keep ADR-0028's two-round cap, its adjudication rule and its ban on the author answering the reviewer. Replace its severity bar. A finding about code the feature changed is fixed before the feature closes. It is filed as an ISS-* only when the fix needs a product decision, touches code the feature did not change, or is too large for the session. A finding that is neither fixed nor worth filing is recorded in the feature's review section and dropped. A review covers one feature's diff, follows a fixed procedure and stops at a budget."
context: "ADR-0028 stopped review loops. It did so by letting every true finding that does not break behaviour be filed at triage while the item closes. In your-trainer, that turned a review's findings into backlog: 55 of 121 open issues come from reviews, and FEAT-0107's main behaviour has no test that can fail, which was filed as ISS-0466 instead of fixed. A single review still takes about 160 turns and 90-100 tool calls, because it has no scope limit, no procedure and no stopping point."
alternatives: ["Keep ADR-0028 and triage the backlog more often", "Block on every true finding again, with the round cap kept", "Fix-first with a filing bar (chosen)", "Stop independent review and rely on tests"]
consequences: ["QUALITY.md: the severity bar bullet is replaced by the fix-first rule and the filing bar", "independent-review/SKILL.md: step 3 asks for blocking findings in full and the rest as a short list; step 5 fixes before it files; a budget and a fixed procedure are added", "LIFECYCLE.md 'Scope of a change' no longer applies to code the current feature changed", "The issue template gains reported_by and a user-visible first line; a waiting-on-Edwin issue must state its question, options and a recommendation", "Reviews may run on a cheaper model where a trial shows no loss (ADR-0013 already says context, not model, makes a review independent)"]
supersedes: ""
superseded: ""
related: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]", "[[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]"]
---

# A finding is fixed in the feature that caused it, and a review is sized to the change

## Context

The measurements are in [[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT|the 2026-09-18 reference note]]. In short:

- **Reviews stopped looping but are still large.** Since ADR-0028, every gate runs once or twice. A single review is still about 160 turns and 90–100 tool calls. On 2026-09-17, your-trainer spent about 2.7 hours reviewing five features.
- **Review findings become backlog.** In your-trainer, 55 of the 121 open issues come from reviews. Four findings against FEAT-0107's own code were filed on the day of its review. One of them, ISS-0466, says the feature's main behaviour has no test that can fail: deleting all six guards left 1322 tests passing.
- **The backlog is not true.** 34 issues from a review on 2026-03-01 were never revisited. At least one, ISS-0078, describes code that no longer exists.
- **Decisions get pushed to Edwin.** 16 open issues in your-trainer say they wait on him. Most do not state a question he could answer.

ADR-0028 chose "only a behavioural finding blocks" to stop reviews from looping on small points. It worked for loops. Its side effect is that "does not block" became "is filed and forgotten".

## Decision

1. **The round cap stays.** ADR-0028's two rounds, its adjudicated exchange and its rule that the author never answers the reviewer in turns are unchanged.
2. **A finding about code the feature changed is fixed before the feature closes.** Blocking now decides only whether a second round runs. It no longer decides whether the fix is made. A test that cannot fail on the feature's main claim counts as a finding about that feature.
3. **A finding is filed as an `ISS-*` only when:**
   - the fix needs a product decision; or
   - the defect is in code the feature did not change; or
   - the fix is too large to finish in the session.

   Anything else is fixed, or recorded in the feature's review section and dropped. Wording in notes, a figure that does not reproduce, and a duplicated history line are not issues.
4. **An issue says what a user would notice.** The title and the first sentence name the symptom in plain words. The issue records `reported_by:` (`user:<name>`, `review` or `agent`).
5. **A question for the owner is asked, not filed.** If a sensible default exists, the agent takes it and says so in the close-out summary. An issue may wait on the owner only if it states the question, the options and a recommendation.
6. **A review is sized to the change.** It covers one feature's diff, or several small features that close together, never a whole phase again. It follows a fixed procedure:
   1. Run the tests once.
   2. Check each acceptance criterion against the diff.
   3. Break the two or three guards the feature depends on most, and confirm a test fails each time.
   4. List anything else seen, with no further digging.

   It stops at about 40 tool calls.

## Alternatives

- **Keep ADR-0028 and triage more often.** Rejected. It keeps producing issues that need a person, and nobody triages. The March review's 34 issues show what happens.
- **Block on every true finding again.** Rejected. That is the eight-round loop ADR-0028 ended.
- **Stop independent review.** Rejected. The FEAT-0107 review found a main behaviour with no test that can fail. Reviews do find what the author misses; the problem is what happens to the finding afterwards.

## Consequences

- `QUALITY.md`, `independent-review/SKILL.md`, `LIFECYCLE.md` ("Scope of a change"), the close-out skill and the issue template change in `~/Dev/repos/project-os`. Every repo receives them at the next sync.
- A feature may take longer to close, because it now carries its fixes. A review is expected to take a third of its current tool calls.
- Round counts are still recorded nowhere until [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] lands. The new budget is also convention rather than check until then.
