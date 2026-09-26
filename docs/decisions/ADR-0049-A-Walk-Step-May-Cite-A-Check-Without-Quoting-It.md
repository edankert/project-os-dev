---
type: "[[adr]]"
id: ADR-0049
aliases: ["ADR-0049"]
title: "A walk step may cite a check's step without quoting it, and the sheet prints the check's current words"
status: accepted
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully and on the open issues .. ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
decision: "A procedure's expectation line may be its tags alone. The sheet and the cockpit print the check's current Expect text for it: line N for `.N` when the check has one Expect line per numbered step, otherwise every line. Quoted lines keep working and are still compared word for word; walk-tags.py rewrites them as tags where that prints the same words, and re-quotes them from the check when it is reworded."
context: "ADR-0045 requires each expectation line to quote the check word for word, so rewording a check breaks every walk that quotes it."
alternatives: ["Keep the quote rule and fix each walk by hand", "Generate the whole expectation text into the procedure file"]
consequences: ["Rewording a check changes what the next sheet prints and breaks no tag-only walk", "A tag-only line on a check whose steps and Expect lines do not pair prints all of that check's Expect lines", "Quoted lines still break on rewording until walk-tags.py --refresh re-quotes them"]
supersedes: ""
superseded: ""
amends: "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
decided_option: "1"
decided: 2026-09-26
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]", "[[PHASE-0009-A-Change-Costs-Only-Its-Own-Work]]", "[[TASK-0175]]"]
---

# A walk step may cite a check's step without quoting it, and the sheet prints the check's current words

## Context

ADR-0045 made a procedure's expectation line quote the check's own `## Expect` line word for word, and the validator compares the two. The reason still holds: a tick recorded from a procedure step stands as a verdict on the check itself only if the walker read the check's own words (project-os-cockpit ADR-0041).

The cost showed up in your-trainer on 2026-09-26 (ISS-0088). Rewording TST-0480 and TST-0626 broke two walk files, and fixing them surfaced a third check, TST-0483. Every reworded check means a second edit in every procedure that quotes it.

Measured on your-trainer the same day: 956 quoted lines in 11 procedures. 308 of them quote checks that state no Expect text, which the validator does not compare. 49 checks have exactly one Expect line per numbered step, and on those, 204 of 211 quotes citing step N quote Expect line N.

## Options

1. **A line may be its tags alone, and the generator prints the check's current words for it.** The walker still reads the check's own words, so the tick keeps its meaning. Rewording a check changes the next sheet and breaks nothing.
2. **Keep the quote, and fix each walk by hand.** What happens today.
3. **Generate the expectation text into the procedure file.** The file then holds a copy that goes stale the same way, and the generator writes into authored text.

## Decision

**Option 1**, as the ISS-0088 report proposed and Edwin asked for it to be built on 2026-09-26 ("ISS-0088 also as suggested").

- **A tag-only line** is `` - `TST-0480.1` ``. The sheet and the cockpit's payload print the check's current Expect text in its place, each line carrying the tag.
- **Which lines it prints.** When a check has exactly one Expect line per numbered step, `.N` prints line N, which is how walks already quote those checks. Otherwise a tag prints all of the check's Expect lines, because nothing in the check says which line belongs to which step.
- **Quoted lines keep working**, compared word for word as ADR-0045 decided. `tools/scripts/walk-tags.py` rewrites a quoted line as its tags wherever the tag prints exactly the quoted words, and leaves every other line alone. `walk-tags.py --refresh` re-quotes a line whose check was reworded: it finds the check's last version that had the quoted words and takes the current line at the same position, if the section still has as many lines.
- **ADR-0045 is amended, not replaced.** Its decision 4 now allows tag-only lines. Everything else in it stands.

## Consequences

- Rewording a check breaks no tag-only walk.
- A tag-only line on an unpaired check prints more than one expectation. An author who means one of several lines quotes it.
- A quoted line still breaks when its check is reworded, until `walk-tags.py --refresh` is run. The validator's message says so.
- The cockpit shows the current words once its bundled copy of `walk-sheet.py` is refreshed, since the expansion happens in that module.

## Acceptance

- [x] Tag-only lines print the check's current words on the sheet and in the payload (TASK-0175, `test-walk-sheet.sh`).
- [x] Quoted lines still work, and the converter rewrites them where nothing is lost (TASK-0175).
- [x] TESTING.md "The walk", rule 9, the walk-procedure skill and the procedure template say so (TASK-0175).
