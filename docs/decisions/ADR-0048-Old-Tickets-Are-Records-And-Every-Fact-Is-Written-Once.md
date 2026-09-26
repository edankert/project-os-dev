---
type: "[[adr]]"
id: ADR-0048
aliases: ["ADR-0048"]
title: "Finished tickets are frozen records, standing records are superseded in one place, and every relationship is written once"
status: accepted
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["Edwin, 2026-09-26: 'Would it for instance make sense if we always assume later decisions and tickets overrule previous tickets and decisions or should we update the scan/validate/check scripts to only work with later (not completed or not released) tickets?'", "your-trainer session your-trainer-b8, time review, 2026-09-26 (ISS-0087 to ISS-0092)"]
decision: "Option 4, accepted by Edwin 2026-09-26: a ticket is frozen once its release is out; supersession is written once in the new note and a tool writes the back-pointer into the old one; an edit to a frozen ticket is a warning, not an error, so unforeseen corrections stay possible. Every relationship is written once, on the child, and the reverse lists are derived; a content rule judges only notes open when it arrived; the tools parse each note once and cache it."
context: "Agents spend most of a session's time keeping older notes consistent and waiting on checks that re-read every note, not on the change itself."
alternatives: ["Keep reconciling old tickets", "Later notes overrule earlier ones with no pointer", "Run the tools only on live notes"]
consequences: ["Authors write each fact once and never edit a released ticket", "Hand-written reverse lists become generated", "Pre-commit and Stop hooks fall to seconds once parsing is shared and cached (estimated)", "Tools gain an optional libyaml dependency with the current parser as fallback"]
supersedes: ""
superseded: ""
decided_option: "4"
decided: 2026-09-26
related: ["[[PHASE-0009-A-Change-Costs-Only-Its-Own-Work]]", "[[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold]]", "[[ISS-0091-Finished-Notes-Have-No-Archive]]", "[[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link]]", "[[ADR-0009]]", "[[ADR-0011]]"]
---

# Finished tickets are frozen records, standing records are superseded in one place, and every relationship is written once

## Context

A your-trainer session on 2026-09-26 answered a user's question with a two-call-site code change and one test, and spent almost all of its time on documentation upkeep (ISS-0087 to ISS-0092). Edwin asked whether later notes should simply overrule earlier ones, or whether the checking scripts should only look at work that is not yet finished or released, and why the scripts take so long.

Measured on 2026-09-26:

- **The checks are slow because they parse the same notes repeatedly, not because there are many notes.** your-trainer has 3,150 notes. A commit spends about 54 seconds in the pre-commit hook: `sync-snapshot.py` 14.5 s, `validate-docs.py` 28.1 s and `walk-sheet.py --check` 11.2 s, each reading every note again. Inside the validator, `parse_frontmatter` runs 16,402 times for those 3,150 notes, about five times each, and is 79% of the run. Parsing each note once cut the validator from 28.6 s to 10.3 s with identical output. PyYAML's C loader, present on this machine, parses all the notes in 0.32 s, against 4.2 s pure-Python and about 7 s for the validator's own parser. Checking whether a note changed costs 8 ms for all of them. The Stop hook runs the same validator, so every stop after a write pays about 40 s. The weekly link checker in CI is not part of this.
- **Half the validator's output is about finished notes.** Of 1,139 findings in your-trainer, 581 (51%) are about notes already finished. About 315 come from rules introduced after those notes closed (`VERIFY-ACCEPTANCE` 130, `REQ-BOXES` 118, `FEATURE-REQ` 30, `FEATURE-UNCOVERED` 26, `REVIEW-STALE` 11). 654 are `LEDGER-FIELD`, leftovers of one migration.
- **One fact is written in several places by hand.** Adding a task to a feature in a phase writes the same membership six times: the task's `parent:` and `phase:`, the feature's `tasks:`, the phase note's `tasks:`, and three lists in the snapshot. `PARENT-BACKLINK` and `SNAPSHOT-MEMBERSHIP` exist to catch the copies drifting, and ISS-0084 was a copy that drifted silently. The your-trainer session applied later decisions about one parked feature across up to eleven notes.

## Options

1. **Keep reconciling.** Every later decision is carried back into the older notes it affects. Correct, and it is the cost being measured.
2. **Later overrules earlier, with no pointer.** Nothing old is edited, and a reader assumes anything newer wins. This fails for the way agents actually reach notes: by following a link or an id (TESTING.md cites "ADR-0045 decision 5"; code comments cite ADRs), by grep, whose results come in path order and put ADR-0045 before ADR-0046, and by the snapshot, which lists only work in flight. None of these is newest-first, and PHASE-0008 measured that ranking by recency finds about a quarter of what a session goes on to read. An agent that lands on an old ADR has no way to know a newer one replaced it, so to be safe it must search for one each time, which costs more than option 1.
3. **Run the tools only on live notes.** Less output, but little faster: the index still has to read every note, because live notes link to finished ones and counters span every id. The time is in re-parsing, which option 4 removes directly. It also leaves the six-places problem untouched.
4. **Separate records by kind, write each fact once, and derive the rest.**
   - **A ticket (task, issue, change note, acceptance run) is a record of an event.** Once the release that shipped it is out, it is frozen: never edited to match later work, apart from a supersession pointer that tooling writes. Until then it may still change, which the your-trainer session needed.
   - **A standing record (ADR, requirement, feature, active acceptance check, phase) describes how things are.** It is changed by amendment or supersession, never left to be overruled silently.
   - **Supersession is written once, in the new note** (`supersedes: [[ADR-0045]]`), which is what Edwin proposed. The back-pointer on the old note is derived, not authored: `sync-snapshot.py` stamps `superseded_by:` and the status, `snapshot-query.py` shows it, and the validator warns when a live note cites something superseded. Nobody opens the old note to keep it current, and an agent that reaches it by a link is still told.
   - **Every relationship is written once, on the child** (`parent:`, `phase:`, `implements:`, `supersedes:`). The parent's `tasks:`, the phase's lists and the snapshot's membership are generated, as statuses already are (ADR-0009).
   - **A content rule judges only notes still open when the rule arrived.** Structural checks (links resolve, ids unique, frontmatter parses, counters) still cover every note.
   - **The tools parse each note once, with libyaml where present, and cache by path, size and mtime across runs and across scripts.** A second run re-reads only what changed.

## Decision

**Option 4, accepted by Edwin on 2026-09-26.**

> [!quote] Decided — 2026-09-26 (user:edwin)
> 1. when its released, okay write it in the old note, I don't know what this would mean error or warning, I think warning we need to allow editing frozen tickets for unforeseen circumstances?

- **Freeze boundary:** a ticket is frozen once the release that shipped it is out.
- **Back-pointer:** a tool (`sync-snapshot.py`) writes it into the old note; nobody writes it by hand.
- **Enforcement:** an edit to a frozen ticket is a **warning**, not an error, so a correction nobody foresaw can still be made. The warning names the ticket, so the edit is a visible choice rather than routine upkeep.

## Alternatives

- Option 1: what happens today.
- Option 2: fails because agents do not reach notes newest-first. Kept as the reason the back-pointer in option 4 is generated rather than dropped.
- Option 3: kept as part of option 4, for output only (a `--changed` view), not as the performance fix.

## Consequences

- An author writes each fact once and never edits a released ticket. The upkeep the your-trainer session measured goes to the tools.
- Existing hand-written reverse lists become generated; `PARENT-BACKLINK` and parts of `SNAPSHOT-MEMBERSHIP` retire, because nothing is copied that could drift.
- The pre-commit hook and Stop hook should fall from about 54 s and 40 s to a few seconds in your-trainer, once parsing is shared and cached. That estimate follows from the measurements above and is not yet measured end to end.
- Tools gain an optional dependency on libyaml, with the current parser as the fallback, so a machine without it is no slower than today.
- Finished-note archiving (ISS-0091) becomes cheap: a frozen, released ticket can move without anything having to follow it.

## Acceptance

- [x] Edwin decides the option, and for option 4 the three threads below — option 4, 2026-09-26
- [x] The freeze boundary — when its release is out (Edwin, 2026-09-26)
- [x] The back-pointer — written into the old note by the tool (Edwin, 2026-09-26)
- [x] Enforcement — a warning, so unforeseen corrections stay possible (Edwin, 2026-09-26; the draft had proposed an error)

## Implementation, filed 2026-09-26

ISS-0093 (parse once, libyaml, cache), ISS-0094 (rules judge only notes open when they arrived), ISS-0095 (reverse lists derived), ISS-0096 (supersession written once, back-pointer derived), ISS-0097 (released tickets frozen), ISS-0098 (notes hold current state), ISS-0099 (LEDGER-FIELD migration), ISS-0100 (measure the time spent on finished notes, before and after). ISS-0087, ISS-0091 and ISS-0092 are related work already filed.
