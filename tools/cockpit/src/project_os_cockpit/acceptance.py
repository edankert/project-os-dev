"""The acceptance-test suite and the release gate it makes possible (TASK-0373).

`tools/instructions/TESTING.md` has described Tier 1 / Tier 2 / Tier 3, the
re-run rule and *"a release is blocked while any Tier 1/Tier 2 test is
unchecked"* since the template was written. **No repo had ever instantiated
it.** Measured 2026-08-10 across the twelve the cockpit renders: 92 ``TST-*``
notes, zero tier classification, and a gate that had never been able to fire.

This module reads ``docs/tests/ACCEPTANCE_TESTS.md`` and answers two questions:
what the tiers hold, and what is blocking a release.

**Why parse a checklist rather than read frontmatter.** Tier is a property of a
*checkbox*, not of a note — Tier 1 is "one or more per feature" covering
user-visible behaviour, while a ``TST-*`` is usually one pytest module covering
an internal contract. TESTING.md is explicit that the two systems coexist. A
``tier:`` field on the notes would tier the wrong objects and leave the box the
gate actually reads with nowhere to live.

The format is the template's own, so nothing here invents a convention:

    # Tier 1 — Feature Tests
    ## 1.1 Some area ([[FEAT-0001]], [[FEAT-0002]])
    - [ ] **Name:** procedure and expected result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace, field
from pathlib import Path
from typing import Any

#: Where the suite lives. TESTING.md names this path; it is not configurable,
#: for the same reason `SNAPSHOT.yaml` is not — a checklist the gate cannot
#: find is a gate that silently passes.
SUITE_REL = "tests/ACCEPTANCE_TESTS.md"

#: Where checks live once they are notes ([[ADR-0030]]). The sibling of
#: `SUITE_REL`, and **never both**: a repo that migrates deletes the file in
#: the migration commit, because a left-behind copy is the dual-source trap
#: this project has paid for twice. `load()` below reads whichever exists and
#: says which shape it found, so the two can coexist across the fleet — which
#: they must, since the repos migrate one at a time.
CHECKS_REL = "tests/acceptance"

#: **`GATING_TIERS` and `PERMANENT_TIERS` are gone** (ADR-0039). Both were
#: `(1, 2)` -- one constant written twice and read as two different questions,
#: *does this gate a release* and *does this test still apply*. Neither is a
#: tier question. The answer to both is now `MANUAL_SECTIONS`: an unsettled
#: manual check blocks, and an automated one never enters the list.

#: A `- [ ]` inside a code fence is an *example* of a checkbox, not one. Found
#: by re-review (ISS-0141): `criteria.py` and the validator's box counter both
#: skip fences deliberately and this module did not, so a documentation example
#: in the suite would have been a real, blocking, unwalkable gating item — and
#: the raw-line guard could not have seen it, because raw and parsed would both
#: have counted it. Same regex as `criteria.FENCE_RE`, restated rather than
#: imported to keep this module free of a dependency it otherwise has no use
#: for; `test_a_checkbox_inside_a_code_fence_is_an_example` pins the pair.
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_TIER_HEADING_RE = re.compile(r"^#\s+Tier\s+(\d)\s*[—-]\s*(.+?)\s*$", re.M)
_SECTION_RE = re.compile(r"^##\s+(\d+\.\d+)\s+(.*?)\s*$")
#: **Any** bullet, **any** mark, decided below rather than filtered here
#: (ISS-0141). The first version matched `^-\s+\[( |x|X)\]`, which gave the
#: parser a way to say nothing: `- [~]` — the record's own mark for a check
#: settled by decision — was dropped from the suite entirely, along with any
#: typo. A checklist that silently loses lines reports a fuller bar than the
#: document holds, and it feeds a release gate.
#:
#: **The first fix widened the mark and left the line shape alone**, which
#: independent review caught by pointing at ISS-0141's own list of examples:
#: `- [v]` and `- [-]` blocked afterwards, but `- [ x]` — two characters —
#: still vanished, as did an indented `  - [ ]` and a `* [ ]` bullet. Widening
#: one axis of a silent-drop bug leaves the bug. Both axes are open now, and
#: the mark is classified **without stripping**, so `[ x]` is an unrecognised
#: mark (owed, blocking) rather than a line that was never there.
#:
#: *This sentence said "classified after stripping" until the re-review caught
#: it — describing, in the first place a future cleanup reads, precisely the
#: inversion the code below refuses to make. `" x".strip()` is `"x"`, so a
#: parser written from that comment would read a typo as a walked check.*
_ITEM_RE = re.compile(r"^\s*[-*+]\s+\[([^\]]*)\]\s+(.*?)\s*$")
#: **A hard-wrapped row's continuation** (ISS-0216). `_ITEM_RE` matches one
#: PHYSICAL line, and every line it did not match was discarded outright — so a
#: bullet wrapped across three lines parsed as its first line and the rest was
#: dropped with no warning, no count and nothing in the migration's `problems`
#: list. `../your-trainer` carries six notes written from that truncation and
#: `TST-0596`'s entire body is the word `From`.
#:
#: **Indented, non-blank, and not itself a bullet.** Each half is load-bearing
#: and each was measured against the corpus before being written:
#:
#: * *Indented* — the suite's own wrap is six spaces, aligning under the `**`.
#:   Markdown also permits a LAZY continuation at column 0, and accepting one
#:   would be wrong here: the pre-migration file carries 23 unindented `- *…
#:   moved to §3.5*` annotation bullets directly under checkboxes, and they are
#:   separate list items, not the row's text.
#: * *Not itself STRUCTURE* — a nested `  - [ ]` is a check of its own and
#:   `_ITEM_RE` claims it first; a nested `  - plain` is a sub-point rather
#:   than a wrap, and folding it into the parent's prose would invent a
#:   sentence nobody wrote.
#:
#:   **The exclusion is five shapes, not one.** The first version excluded
#:   `-*+` alone, and independent review measured what that let through: an
#:   ordered-list step (`  1. Open the app.`), an indented table, an indented
#:   `##` heading and an indented `>` quote all folded into the row's detail —
#:   *"| col | col | | --- | --- |"* as a sentence. The docstring's own
#:   argument against nested bullets applies verbatim to every one of them.
#:   Unreachable in any committed suite (old and new `parse()` agree over all
#:   137 committed revisions across three repos), and reachable the moment
#:   [[TASK-0531]]'s migration runs, which is the parser it runs through.
#:
#: A blank line, a heading, a fence or the next bullet closes the row.
_CONTINUATION_RE = re.compile(
    r"^\s+(?!(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|>|\|))(\S.*?)\s*$")
#: A line under a checkbox that is unindented, not a bullet and not a heading —
#: Markdown would read it as a LAZY continuation of the row and this parser
#: does not. Reported rather than accepted: the pre-migration corpus puts real
#: `- *… moved to §3.5*` bullets in exactly that position, and guessing wrong
#: would fold a separate annotation into a check's procedure. Reporting says
#: *look at this line* without inventing a sentence nobody wrote.
_LAZY_WRAP_RE = re.compile(r"^(?![-*+#>]|\s|$)\S")
#: Walked. `X` is Markdown-legal and appears in the wild.
_CHECKED_MARKS = frozenset({"done", "x", "X"})
#: Settled by a decision rather than by being walked — the check describes a
#: surface that was retired, or asks for a precondition that cannot be made.
#: It does not block; it is counted and named, which is the difference between
#: reconciling something and losing it.
#: `[/]` is Minimal's *incomplete*; `[~]` is the legacy alias, read forever and
#: never written. Every one of `../your-trainer`'s seven `~` rows says
#: *"Partial pass"*, which is why `~` aliases `/` and not `-` — an earlier
#: draft had it the other way and the rows corrected it (ADR-0029).
_RECONCILED_MARKS = frozenset({"incomplete", "/", "~"})
#: **Shipping anyway** (FEAT-0104). A check that is not done, on a release
#: somebody has decided to ship regardless. `TESTING.md` line 113 has always
#: allowed this — *"A test may be marked as a release exception if it cannot
#: be completed … Exceptions must be documented in the release note with
#: justification"* — and nothing has ever implemented it.
#:
#: Reported SEPARATELY from `~`, never folded into it. Both are non-blocking,
#: and there the resemblance stops: `~` is permanent and says the check no
#: longer applies; `!` is **per-release** and says the check still applies and
#: was not done. Conflating them would lose exactly the difference ISS-0141
#: exists to protect, and would make an exception look settled forever when it
#: expires with its release.
#: `[-]` is Minimal's *canceled*, and is where the release exception moved
#: (ADR-0029). The concept is unchanged — a check that will not be done and is
#: not holding the release — and it keeps its field and its separate count.
#: Only the character changed, from the `[!]` this project minted and which was
#: written in zero suites fleet-wide.
_EXCEPTED_MARKS = frozenset({"canceled", "-"})
#: **Failed, and tracked** (TASK-0454). `../your-trainer`'s own suites use this
#: with a dated verdict and a linked issue — *"`[F]` … **FAILS 2026-06-07** —
#: collapse state is stored globally … Tracked as [[ISS-0285]]"*.
#:
#: It is named here **without** being added to any non-blocking set, because
#: the parser already reads an unrecognised mark as blocking and for a
#: failed-and-tracked check that is the right answer. Naming it changes only
#: what the surface can SAY — `failed`, rather than a shrug — and the mark's
#: effect on the gate is deliberately identical to what it was before.
#:
#: Recorded so nobody later reads `[F]`-is-blocking as a parser gap and
#: "fixes" it into a pass. A check that failed is not a check that passed.
#: `[!]` is Minimal's *important*; `[F]` is the legacy alias.
#:
#: **`[!]` REVERSES MEANING HERE** (ADR-0029). It was a release exception and
#: did not block; it is *failed* and does. Safe only because the mark is
#: written in zero suites across twelve repos, verified before the decision
#: rather than after — any `[!]` authored in the one day it meant the opposite
#: would silently begin blocking a release.
_FAILED_MARKS = frozenset({"important", "!", "F"})
#: `[?]` is Minimal's *question* — the walker read the check and cannot tell
#: what it is asking. **Blocks**, and it is a third blocking mark that means a
#: third thing: `[ ]` nobody looked, `[!]` somebody looked and it broke, `[?]`
#: somebody looked and could not tell. Collapsing any pair loses the
#: distinction the vocabulary exists for.
_QUESTION_MARKS = frozenset({"question", "?"})
#: **Walked, then invalidated by a later change** (ADR-0034 decision 5). The
#: seventh value, and the one the character vocabulary could not express: an
#: invalidated check was written `mark: " "` — *"nobody has walked it"* — plus
#: an `invalidated_by:` block, so the two states were the same value in the one
#: field every surface reads. **Blocks**, like every other unsettled value.
#:
#: It has no legacy character, deliberately. `LEGACY_MARKS` maps `" "` to
#: `todo`, which is what an unmigrated repo means by it; the invalidation is
#: still carried there by `invalidated_by:` and recovered by comparing dates,
#: exactly as it was before.
_RERUN_MARKS = frozenset({"rerun"})
#: A check that is ticked but whose evidence was invalidated by a later change.
#: `TESTING.md` rule 2 says a code change unchecks the tests it overlaps; the
#: practice in `../your-trainer` is softer — the tick stays and the row gains
#: `RE-RUN (TASK-0385: AddUserScreen replaced by inline dialog)`.
#:
#: **54 rows carry one and 53 are still ticked**, so the gate counts 53 rows as
#: passed on evidence their own line says is stale, and the honest blocking
#: number is 113 rather than 60 (TASK-0448).
#:
#: The parenthetical is REQUIRED by this pattern, which is what keeps the
#: suite's own `## Rules` line — *"After a verified release: Tier 3 tests are
#: removed, RE-RUN annotations are cleared"* — from being read as an
#: annotation. That line is also outside any tier heading, so it is skipped
#: twice over; belt and braces, because a rule that swept up its own
#: description would be silently self-referential.
_RERUN_RE = re.compile(r"\bRE-RUN\s*\(([^)]*)\)")
#: **Burden tags are deliberately not parsed here** (TASK-0449, resolved `[~]`).
#:
#: The plan was to order the gate's rows by what a walker needs at hand, using
#: the tags `../your-trainer`'s `TST-0013` puts on all 107 of its rows —
#: `[App]` 98, `[Trainer]` 21, `[Strava]` 8, `[icu]` 6, and so on. Two
#: measurements killed it, both taken before any of it shipped:
#:
#: 1. **`ACCEPTANCE_TESTS.md` carries none.** The document the gate actually
#:    reads has zero burden tags in every repo in the fleet. A scanner written
#:    for it found six, and **all six were false positives** — `[Debug]` from
#:    inside a quoted workout name, *"verify no workouts with `[Debug]` prefix
#:    appear"*. A 6-of-6 false-positive rate on the only corpus it would run
#:    against is not a heuristic that needs tuning; it is the wrong idea.
#: 2. **`TST-0013` is not a suite.** It has no `# Tier N` heading, so `parse`
#:    yields **0 items** for it. The one document carrying real tags is a
#:    `TST-*` read by `manual_test_steps`, which this module never sees.
#:
#: The task's own scope note said a heuristic inferring burden from prose was
#: out of scope because *"it would be wrong quietly"*. It would have been.
#:
#: The **purpose** — do not make someone stand a trainer up twice — is already
#: served: FEAT-0102 groups the gate by section, and section is the sitting.
_NAME_RE = re.compile(r"^\*\*(.+?):?\*\*:?\s*(.*)$")
_ID_RE = re.compile(r"\[\[([A-Z]+-[0-9A-Za-z-]+?)(?:\|[^\]]*)?\]\]")
#: Bare `FEAT-0104`, which is how every suite in the fleet actually writes it
#: (ISS-0173). Wikilink form was the only form read, and **not one heading in
#: `your-trainer`'s 1082-line suite uses it** — 72 of its 82 section headings
#: name a feature or issue and the parser found zero. Two things went wrong at
#: once: `missing_issue_refs` reported **158 of 158** Tier 2 items as
#: violating TESTING.md's rule (a check nothing consumed, which is why it went
#: unnoticed), and the row -> subject link a scoped gate needs did not exist as
#: far as any code could tell. The same shape as ISS-0162's 48 bare ADR
#: citations: the record said the right thing in a form the reader refused.
_BARE_ID_RE = re.compile(r"\b([A-Z]{2,6}-\d{3,4})\b")
#: **Only** the trailing parenthetical, so a heading mentioning an id in prose
#: — *"Handles TASK-0132-style imports"* — does not acquire a false subject.
#: Not a guess about where authors put them: measured across every suite in the
#: fleet on 2026-08-16, **114 of 114** id-bearing headings put all of theirs
#: here, and `area` below already strips exactly this span for the same reason.
_TRAILING_PAREN_RE = re.compile(r"\(([^()]*)\)\s*$")


def heading_refs(heading: str) -> tuple[str, ...]:
    """Project-os ids a section heading names, in document order.

    Wikilinked ids anywhere; bare ids in the trailing parenthetical only.
    """
    refs: list[str] = list(_ID_RE.findall(heading))
    tail = _TRAILING_PAREN_RE.search(heading)
    if tail:
        for note_id in _BARE_ID_RE.findall(tail.group(1)):
            if note_id not in refs:
                refs.append(note_id)
    return tuple(refs)


@dataclass(frozen=True)
class Invalidation:
    """`RE-RUN (TASK-####: reason)`, structured — TESTING.md rule 3 as a field.

    The annotation is the corpus's own invention, hand-written 54 times in
    `../your-trainer` and read by nothing until [[TASK-0448]]. Structuring it is
    half of what [[ADR-0030]] buys: `change` is resolvable through the index,
    `date` makes staleness arithmetic, and `raw` keeps the annotation's exact
    inner text so a migration can be proved lossless rather than assumed to be.

    **`raw` is not redundant with the other three.** 26 of the 54 annotations
    put the id somewhere the `ID: reason` shape does not describe, and a
    structured triple that silently dropped their wording would lose the only
    account of why a tick stopped being trustworthy.
    """

    change: str = ""
    reason: str = ""
    date: str = ""
    #: The annotation's inner text verbatim, exactly as `rerun` has always
    #: reported it. Every existing consumer reads this and is unaffected.
    raw: str = ""

    def __bool__(self) -> bool:
        return bool(self.raw or self.change or self.reason)


#: The empty invalidation, so `Item`'s default is one shared frozen instance
#: rather than a factory nobody would notice was being called 579 times.
_NOT_INVALIDATED = Invalidation()


@dataclass(frozen=True)
class Item:
    """One checkbox — the unit the gate reads.

    **Two storage shapes, one class** ([[ADR-0030]]): a row parsed out of
    `ACCEPTANCE_TESTS.md`, or a `CHK-*` note. Every consumer — the gate, the
    delta, the Tests view, the release page — reads this and cannot tell,
    which is what let the migration land without a second renderer. The
    note-shape fields below default to empty, so a file-shape item is exactly
    what it always was.
    """

    tier: int
    section: str          # "1.3"
    area: str             # "The navigator"
    name: str
    text: str
    #: Walked, with evidence on the line.
    checked: bool
    #: Settled by a decision instead (ISS-0141). Never both — a mark is one
    #: thing — and anything the parser cannot classify is neither, so it is
    #: owed and blocks. That is the direction that fails safely.
    reconciled: bool = False
    #: A release exception: not done, and shipping anyway (FEAT-0104).
    excepted: bool = False
    #: The check was read and is not understood (`[?]`). Blocking, and
    #: distinct from unwalked: somebody looked.
    question: bool = False
    #: Walked and failed, with the failure tracked on the line (TASK-0454).
    #: Blocking — `settled` deliberately does not consult this — and named so a
    #: surface can distinguish *"nobody has walked this"* from *"somebody
    #: walked it and it failed"*, which are the same colour today.
    failed: bool = False
    #: **Walked, then invalidated by a later change** (ADR-0034 decision 5).
    #: Blocking, and the state the character vocabulary could not say: an
    #: invalidated check was `mark: " "` — *"nobody has walked it"* — beside an
    #: `invalidated_by:` block, so a check somebody walked and one nobody has
    #: touched were the same value in the field every surface reads.
    needs_rerun: bool = False
    #: The invalidation, structured. `rerun` below is the string every existing
    #: caller already reads, kept as a property so the two cannot disagree —
    #: which they would within a week if both were fields set side by side.
    invalidated: Invalidation = _NOT_INVALIDATED
    #: The mark as a WORD, normalised on read by :func:`normalise_mark` —
    #: `todo`, `done`, `incomplete`, `canceled`, `important`, `question`,
    #: `rerun`, or whatever nobody recognises. A note authored with a character
    #: (an unmigrated repo, or any of the twelve historical tags `suite_at`
    #: reads) arrives here already translated, so nothing downstream carries a
    #: second vocabulary.
    #:
    #: The five booleans above are *classifications* of this, and they are
    #: lossy on purpose: `x` and `X` are one thing to the gate, and so are `/`
    #: and `~`. A surface that DRAWS the mark needs the character back, and
    #: until [[ISS-0190]] it could not have it — `parse` read the mark,
    #: derived five flags from it and dropped it on the floor.
    mark: str = " "
    #: 1-based position within its section, so every item has a unique number
    #: (`1.3.2`). Two items in one section otherwise share the section's id,
    #: and a navigator that keys rows on it would address the wrong one.
    ordinal: int = 1
    #: Project-os ids named by the section heading. Tier 1 sections name their
    #: features; Tier 2 sections name the `ISS-*` that created the test, which
    #: TESTING.md requires and `missing_issue_refs` enforces.
    refs: tuple[str, ...] = ()
    #: The section heading VERBATIM, so a link can slugify exactly what the
    #: renderer slugified (FEAT-0103). Reconstructing it from `section` and
    #: `area` does not work — `area` has the id parenthetical stripped and the
    #: rendered anchor keeps it, so the two differ by precisely the part that
    #: makes the link land.
    heading: str = ""

    # ----- note shape only (ADR-0030). Empty on a row parsed from a file. ---
    #: `CHK-0001`, so a surface can address the check itself rather than a
    #: position in a document. The whole point of the migration: `number` is an
    #: address that MOVES, and this one does not.
    note_id: str = ""
    #: The note's docs-relative path, so a row can open it.
    rel: str = ""
    #: `draft` / `active` / `retired` — the LIFECYCLE. Never the verdict.
    status: str = ""
    #: When the current `mark` was recorded, and why. `verdict_reason` is
    #: required for `/`, `-`, `!` and `?`; the write path refuses without one.
    verdict_date: str = ""
    verdict_reason: str = ""
    #: **How a machine executes this check, and the field the reader never had**
    #: ([[ISS-0237]]). `item_from_note` did not look at `command:` at all, so
    #: every consumer -- the gate, the sections, the percentage -- treated an
    #: automated check as one a person owed. Measured 2026-08-19: 89 checks in
    #: `your-trainer` carry one, and **nine of the 68 blocking its release were
    #: executed by a machine**.
    command: str = ""
    #: `full` / `partial` / `manual`, and what supplies the coverage. Rolled up
    #: as a release's *confidence*, which is why it is a check property and not
    #: — as first proposed — a feature stat.
    automation: str = ""
    #: **`covered_by:` is gone** ([[REQ-0057]], [[FEAT-0138]]). A note no
    #: longer declares that a machine covers it: the claim rotted silently --
    #: rename, delete or disable the covering test and the note kept asserting
    #: coverage while the check left the run list permanently, with no signal.
    #: The test declares the check now (`# Covers: TST-####`) and the RUN emits
    #: a `method: automated` verdict into the ledger, so deleting the test
    #: stops the emission and the check reappears on its own. The field held
    #: nothing on 671 of 671 notes fleet-wide ([[ISS-0198]]), so removing it
    #: took nothing away.
    #: What the walker must have to hand. TASK-0449 was cancelled for the
    #: absence of exactly this field, on the finding that inferring it from
    #: prose was 6-of-6 false positives.
    burden: tuple[str, ...] = ()
    #: Paths, screenshots and log excerpts behind the current verdict.
    evidence: tuple[str, ...] = ()
    #: The pre-migration address (`#section.ordinal`) and the sha the file held
    #: at the cut. Blame does not cross the migration commit (~2% similarity),
    #: so traceability is preserved BY THE RECORD rather than by git plumbing.
    migrated_from: str = ""

    @property
    def rerun(self) -> str:
        """The invalidation annotation's inner text — what `rerun` always was.

        A property rather than a second field: the structured triple and the
        string are one fact, and two fields holding one fact is the shape this
        project keeps paying for.
        """
        return self.invalidated.raw

    @property
    def anchor(self) -> str:
        """The rendered heading's id, so a row can reach its own section.

        Slugified with **markdown's own** function rather than a lookalike.
        These anchors have existed since the suite was first rendered and
        nothing has ever used one; a link that is a single character off lands
        at the top of a 1082-line file, which is the behaviour it replaces.
        """
        from markdown.extensions.toc import slugify

        return slugify(self.heading, "-") if self.heading else ""

    @property
    def settled(self) -> bool:
        """What the gate reads — walked, reconciled, excepted, or **covered**.

        Not "done": a reconciled item was never performed and an excepted one
        is being shipped undone, and the tier counts say so separately.

        **The fourth clause is gone, and its work moved rather than stopped**
        ([[REQ-0057]] / [[FEAT-0138]]). ADR-0031's `covered_by:` clause settled
        a check from a *standing claim in the note*; a machine's coverage is
        now an **event in the ledger**, so it arrives through `mark`/`checked`
        like every other verdict and needs no branch here.

        The direction ADR-0031 protected is unchanged and is now structural: a
        machine's exit code can discharge a person's checkbox, never the
        reverse, because only a run emits `method: automated`. And a covering
        test that fails still un-settles the check — the run appends an
        invalidation, which clears the standing verdict.
        """
        return self.checked or self.reconciled or self.excepted

    @property
    def stale(self) -> bool:
        """Ticked, but the record says the evidence no longer holds.

        Neither blocking nor satisfied — a third thing, and saying so is the
        point. An **unticked** annotated row is already blocking and must not
        be counted here as well, which is what the `checked` conjunct buys.

        **Dates refine this; they do not replace it** (TASK-0466). Once both
        `verdict_date` and `invalidated.date` are known, staleness is
        arithmetic: a pass recorded AFTER the invalidating change answers it,
        and the row stops being stale without anybody clearing an annotation by
        hand — which is TESTING.md rule 3's second half finally being
        performable. Where either date is missing the older rule stands, and
        that is not a fallback for tidiness: **not one** of the 54 annotations
        in the fleet carries a date, so keying staleness on dates alone would
        have reported zero stale rows the day the migration landed and called
        it an improvement.
        """
        if not (self.checked and self.invalidated):
            return False
        #: **Only a feature check is re-opened by a change** (ADR-0039
        #: decision 2). A feature check asserts *the system does X*, and a
        #: later change can falsify that. A regression check asserts *this
        #: defect was fixed* -- a claim about a past event that nothing a
        #: later change does can falsify -- so it is completed once and stays
        #: completed. An automated check is executed by CI and is current by
        #: construction.
        #:
        #: This is the clause carrying the risk, and it is stated so it can be
        #: argued with: nothing re-opens a settled regression check
        #: automatically. If such a bug recurs it files a new issue, and a bug
        #: we expected to recur should have had a `command:`.
        #:
        #: An explicit `mark: rerun` still re-opens anything -- that is a
        #: person saying so, and `needs_rerun` is read separately from this.
        if section_of(self) != SECTION_FEATURE:
            return False
        if self.verdict_date and self.invalidated.date:
            return self.verdict_date < self.invalidated.date
        return True

    @property
    def number(self) -> str:
        """The row's address — its POSITION where it has one, its ID where it
        does not (ISS-0219).

        A file-shape row is always at `section.ordinal`. A note-shape check
        usually is too, because the migration carried both fields across. But a
        check authored *outside* the migration has neither, and
        `f"{'' }.{0}"` made every one of them `".0"` — so two such notes were
        **two checks claiming one address**, and `test_gate_delta` caught it
        the day `your-trainer` gained a second (TASK-0507 relevelled TST-0015
        and TST-0018 out of `docs/tests/`).

        The fallback is the note's own id, which is what [[ADR-0030]] decision
        4 said the address should have become: *"ordinal is display-only and
        sparse … which retires the shifting section-ordinal address for good"*.
        The position survives here only because twelve historical tags hold
        file-shape suites where it is the only address there is.
        """
        #: **The id, whenever there is one** ([[ISS-0224]]). This was the
        #: positional address with the id as a fallback, which [[ISS-0219]]
        #: added because a check authored outside the migration had no
        #: position and every one of them rendered `.0` — two checks claiming
        #: one address. That fix was this decision applied to one case; this
        #: is the general form.
        #:
        #: A file-shape row has no note and keeps its position, which is the
        #: only address it has.
        return self.note_id or f"{self.section}.{self.ordinal}"

    @property
    def key(self) -> str:
        return f"{self.number} {self.name}"


#: How a suite is stored. Three values because a surface has three different
#: things to say: `notes` is post-migration, `file` is pre-migration, and
#: `absent` is the state nine of the twelve fleet repos are in and must never
#: be reported as *"nothing blocking"*.
SHAPE_NOTES = "notes"
SHAPE_FILE = "file"
SHAPE_ABSENT = "absent"


#: A `FEAT-*` id inside a ref that may be a wikilink.
_FEAT_IN_REF = re.compile(r"FEAT-\d+")


@dataclass
class Suite:
    path: Path | None = None
    items: list[Item] = field(default_factory=list)
    #: Which storage answered. Carried rather than inferred from `path`: a
    #: caller that has to look at a filename to know whether it may write row
    #: grammar is a caller that will one day get it wrong.
    shape: str = SHAPE_ABSENT
    #: **Which platform these verdicts are about**, or `""` for the pre-ledger
    #: read. Carried for the same reason `shape` is: a surface that renders
    #: verdicts without naming their platform is the defect [[ADR-0037]] exists
    #: to remove, and a caller that has to remember what it asked for is a
    #: caller that will one day render an Android result as a fact about the
    #: app.
    platform: str = ""

    @property
    def exists(self) -> bool:
        return self.path is not None

    def tier(self, n: int) -> list[Item]:
        """**Deprecated**: `tier:` is read nowhere and nothing writes one
        (ADR-0039). Kept only for the file-shape parser, which still derives a
        tier from a document heading it is reading. Use :meth:`section`."""
        return [i for i in self.items if i.tier == n]

    def section(self, name: str) -> list[Item]:
        """Items in a derived section — `feature`, `regression`, `automated`."""
        return [i for i in self.items if section_of(i) == name]

    def manual(self) -> list[Item]:
        """Every check a person is asked to complete, across both sections."""
        return [i for i in self.items if section_of(i) in MANUAL_SECTIONS]

    def blocking(self) -> list[Item]:
        """Unsettled MANUAL checks — what stops a release.

        `settled`, not `checked`: a reconciled item is a decision the release
        note carries, and blocking on it would make the mark meaningless. An
        item with a mark nobody recognises is neither, so it lands here.
        """
        # The `subjects=None` case of :meth:`blocking_for`, so the release gate
        # and the per-item gate are one predicate rather than two that agree
        # today. Two encodings of one rule is the shape ADR-0032 is about.
        return self.blocking_for(None)

    def blocking_for(self, subjects: "set[str] | None" = None) -> list[Item]:
        """What stops **one item** reaching a terminal status (ADR-0034).

        The general form of :meth:`blocking`, and the whole of Edwin's point
        that gating should work at any granularity: pass the ids an item is
        made of — a feature, or a release and everything in it — and get back
        the unsettled tests covering them.

        **A test covering NOTHING blocks regardless**, and that is the
        fail-closed clause rather than an oversight. A check nobody can
        attribute cannot be discharged by finishing any particular item, so it
        gates the last item there is: the release. Measured on `your-trainer`
        when this was written, **83 of 579 covered nothing** — 74 of them
        Tier 3 and 9 Tier 1/2.

        **All 83 gate now** ([[ADR-0039]]). The sentence above used to add
        *"74 of them Tier 3, which does not gate"*; there is no Tier 3, and a
        one-time check nobody completed and nobody automated is owed like any
        other. That is the decision, not a side effect — see the comment on
        the loop below.

        `subjects=None` means *every* item, which is the release gate and is
        why :meth:`blocking` is this function over the manual sections.
        """
        out: list[Item] = []
        for item in self.items:
            # **Who completes it, not what kind it is** (ADR-0039). This
            # read `tier not in PERMANENT_TIERS`, on the ground that Tier 3 was
            # *"a one-time check for a specific build"* and a check that had
            # stopped applying could not sensibly hold anything open.
            #
            # There is no Tier 3. A check a machine executes carries a
            # `command:` and is not on anybody's list; one that does not is
            # manual and owed. This is still not the gate asking what KIND of
            # test it is or who runs it — the two things REQ-0043 forbids —
            # it is asking whether a PERSON is being asked for anything.
            if section_of(item) not in MANUAL_SECTIONS or item.settled:
                continue
            # **The blind spot is closed, and closing it was decided rather
            # than tidied** ([[ADR-0039]], and this is [[ISS-0208]]).
            #
            # This comment used to describe a TIER FILTER running before the
            # fail-closed clause, so an unattributed Tier 3 check was dropped
            # before the clause meant for it could see it — `your-trainer`
            # carries six (TST-0592..0597, `mark: todo`, never completed).
            # Reversing the order was tried on 2026-08-18 and reverted with the
            # note that it is *"a NEW and tighter gate, which is a decision for
            # a person"*, because TESTING.md then said Tier 3 does not gate.
            #
            # ADR-0039 is that person's decision. There is no Tier 3: a check a
            # machine executes carries a `command:`, and one that does not is
            # manual and owed like any other. **So those six now block**, and
            # the number moves in the direction the earlier attempt measured.
            # TESTING.md no longer says otherwise — its Tier 3 section is gone.
            #
            # Measured against `your-trainer` at HEAD: the gate goes 62 -> 68.
            if subjects is None or not item.refs or (subjects & set(item.refs)):
                out.append(item)
        return out

    def blocking_minus(self, deselected: "set[str] | None" = None) -> list[Item]:
        """The gate when a release has **held features back** ([[TASK-0512]],
        under [[ADR-0040]]).

        **Selection SUBTRACTS; it never divides.** :meth:`blocking_for` is the
        divide reading — pass the subjects and get only the checks covering
        them — and this task was written for that shape before [[ADR-0040]]
        chose the other one. The difference is not academic: measured on
        `your-trainer` 2026-08-20 (working tree), 39 of 59 blocking rows cover
        a `FEAT`, and **36 of those 39 cover a feature the release does not
        carry**. Dividing takes the gate to about 23 on the first render, by
        nobody's decision, and empties the `chronic` bucket whose whole purpose
        is keeping long-carried debt visible.

        So a check is dropped **only** when every subject it names is a feature
        somebody explicitly held back:

        * no `covers:` at all -> gates (the fail-closed clause :meth:`blocking_for`
          already carries, for the same reason);
        * covers an `ISS-*`, `REQ-*` or `PHASE-*` -> gates, untouched by
          selection, because no feature list speaks for it. 20 of
          `your-trainer`'s 59 are in that class;
        * covers a selected feature **and** a deselected one -> gates. Any
          selected subject is enough, and this is the cell a subtraction rule
          gets wrong.

        `deselected` empty or `None` means nothing was held back, so this is
        exactly :meth:`blocking`. **Absence of named contents must not move any
        existing release's gate**, and that is the invariant the task states.
        """
        base = self.blocking()
        if not deselected:
            return base
        out: list[Item] = []
        for item in base:
            refs = [str(r) for r in item.refs]
            if not refs:
                out.append(item)
                continue
            feats = {m.group(0) for r in refs for m in _FEAT_IN_REF.finditer(r)}
            #: A non-feature subject means selection has nothing to say here.
            if len(feats) != len(refs) or not feats:
                out.append(item)
                continue
            if not feats <= deselected:
                out.append(item)
        return out

    def missing_issue_refs(self) -> list[Item]:
        """Manual checks naming no verifiable subject -- no ``FEAT-*``, no ``ISS-*``.

        TESTING.md: *"`covers:` names the `ISS-*` that created it."* A check
        that cannot say what it verifies cannot be told from one that verifies
        something else, and it is classified by default rather than by reading.

        **This asked a tautology for one commit and returned nothing** --
        caught by independent review. Moving it off `tier:` (ADR-0039) had it
        select `section_of(i) == SECTION_REGRESSION and not any(r.startswith
        ("ISS-"))`, and the first clause is true *exactly when* some ref starts
        with `ISS-`, so the two contradict: `your-trainer` went 73 -> 0 and
        `return []` passed the entire suite. That is the same defect this whole
        change is about -- a check reporting nothing because its predicate
        cannot fire -- reintroduced while fixing a review.

        The honest question after the tiers is *which manual check names
        nothing this can verify*, which is `CHECK-SUBJECT`'s domain, so the
        validator and this reader agree by construction.
        """
        return [
            i for i in self.items
            if section_of(i) in MANUAL_SECTIONS
            and not any(r.startswith(("ISS-", "FEAT-")) for r in i.refs)
        ]


def _split_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) == 3 else text


def parse(text: str, *, report: list[str] | None = None) -> list[Item]:
    """Items in document order. Anything outside a tier heading is ignored —
    the template's own preamble is prose, and the Rules section is a numbered
    list that must not be mistaken for tests.

    **A row may be hard-wrapped** (ISS-0216). Its continuation lines are joined
    into one logical row before it is parsed, so a wrapped `**bold name**`
    still yields a name and the detail keeps every word. Before this, the row
    was built from its first PHYSICAL line and the rest was discarded in
    silence — `../your-trainer` carries six notes written from that truncation
    and one of them has the single word `From` for a body.

    Pass ``report`` to collect lines this parser saw under a checkbox and did
    not read as its text. It is deliberately narrow: only *unindented, non-
    bullet, non-heading* lines, which are the ambiguous Markdown-legal "lazy"
    wraps. Ordinary prose between rows is not a loss and is not reported —
    a report nobody can act on is the kind people learn to skip.
    """
    body = _split_frontmatter(text)
    items: list[Item] = []
    tier = 0
    section = ""
    area = ""
    full_heading = ""
    refs: tuple[str, ...] = ()
    ordinal = 0

    #: The row being read, held open until something closes it. A row is not
    #: built at its first line any more (ISS-0216): its text can continue on
    #: the next, and `_NAME_RE` has to run against the WHOLE row or a wrapped
    #: `**bold name**` parses as an unnamed one.
    open_row: dict[str, Any] | None = None

    def close_row() -> None:
        nonlocal open_row
        if open_row is None:
            return
        rest = " ".join(open_row["rest"]).strip()
        named = _NAME_RE.match(rest)
        name, detail = (named.group(1), named.group(2)) if named else (rest, "")
        detail = detail.strip()
        rerun = _RERUN_RE.search(detail)
        mark = open_row["mark"]
        items.append(Item(
            tier=open_row["tier"], section=open_row["section"],
            area=open_row["area"],
            name=name.strip(), text=detail,
            checked=mark in _CHECKED_MARKS,
            reconciled=mark in _RECONCILED_MARKS,
            excepted=mark in _EXCEPTED_MARKS,
            failed=mark in _FAILED_MARKS,
            question=mark in _QUESTION_MARKS,
            needs_rerun=mark in _RERUN_MARKS,
            invalidated=split_rerun(rerun.group(1)) if rerun else _NOT_INVALIDATED,
            mark=mark,
            refs=open_row["refs"], ordinal=open_row["ordinal"],
            heading=open_row["heading"],
        ))
        open_row = None

    in_fence = False
    for line in body.splitlines():
        if _FENCE_RE.match(line):
            close_row()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        tier_head = _TIER_HEADING_RE.match(line)
        if tier_head:
            close_row()
            tier = int(tier_head.group(1))
            section, area, refs = "", "", ()
            continue
        sect = _SECTION_RE.match(line)
        if sect:
            close_row()
            section = sect.group(1)
            ordinal = 0
            heading = sect.group(2)
            refs = heading_refs(heading)
            # The heading minus its id list — "The navigator ([[FEAT-0010]], …)"
            area = re.sub(r"\s*\((?:[^()]*)\)\s*$", "", heading).strip()
            full_heading = f"{section} {heading}".strip()
            continue
        if tier == 0:
            continue
        item = _ITEM_RE.match(line)
        if item:
            close_row()
            ordinal += 1
            open_row = {
                # NOT stripped before comparing: `[ ]` and `[]` are both the
                # plain unchecked box, but `[ x]` is a two-character mark
                # nobody recognises, and stripping it into `x` would silently
                # promote a typo to a walked check — the failure this whole
                # regex exists to stop, inverted.
                "mark": item.group(1), "rest": [item.group(2)],
                "tier": tier, "section": section, "area": area,
                "refs": refs, "ordinal": ordinal, "heading": full_heading,
            }
            continue
        if open_row is not None:
            wrapped = _CONTINUATION_RE.match(line)
            if wrapped:
                open_row["rest"].append(wrapped.group(1))
                continue
            #: Anything else closes the row, and a line that MIGHT have been a
            #: lazy wrap is reported rather than dropped — see `parse_report`.
            if report is not None and _LAZY_WRAP_RE.match(line):
                report.append(
                    f"tier {tier} §{open_row['section']} row {open_row['ordinal']}: "
                    f"unindented line under a checkbox, not read as its text: "
                    f"{line.strip()[:60]!r}"
                )
        close_row()
    close_row()
    return items


#: `TASK-0385: AddUserScreen replaced by inline dialog` — the shape 28 of the
#: fleet's 54 annotations use. The other 26 do not, and this deliberately does
#: not try harder: `raw` keeps every one of them verbatim, so the id is
#: extracted where it is unambiguous and nothing is invented where it is not.
_RERUN_SPLIT_RE = re.compile(r"^\s*([A-Z]{2,6}-\d{3,4})\s*[:—-]\s*(.*)$", re.S)


def split_rerun(raw: str) -> Invalidation:
    """One `RE-RUN (…)` annotation, structured as far as it honestly goes."""
    text = (raw or "").strip()
    found = _RERUN_SPLIT_RE.match(text)
    if found:
        return Invalidation(
            change=found.group(1), reason=found.group(2).strip(), raw=text)
    # No id, or one written in a shape this does not describe. The annotation
    # survives whole; what is not claimed is the structure.
    bare = _BARE_ID_RE.search(text)
    return Invalidation(change=bare.group(1) if bare else "", reason=text, raw=text)


# ----- the note shape (ADR-0030 / FEAT-0113) --------------------------------
#
# The inversion, in ADR-0009's own language: notes are the authored source of
# state and the tool derives. Until this, the acceptance suite was the one
# surface in the system where the stored artifact WAS the display — which is
# why four rounds of marks-control work (ISS-0185..0189) were spent teaching a
# rendered document to behave like a control surface.
#
# Everything below produces the same `Item` the row parser produces. That is
# the whole migration strategy: one model, two readers, and no consumer that
# has to know which one answered.


def _as_tuple(raw: Any) -> tuple[str, ...]:
    """A frontmatter list as strings, tolerating the scalar form authors write."""
    if raw is None or raw == "":
        return ()
    if isinstance(raw, (list, tuple)):
        return tuple(str(x).strip() for x in raw if str(x).strip())
    return (str(raw).strip(),)


def _wikilink_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    """Ids out of `covers:`, in either the `[[FEAT-0001]]` or bare form.

    Both, because the corpus writes both — ISS-0173 is the whole record of what
    reading only one of them costs: 72 of 82 headings named a feature and the
    parser found zero.
    """
    out: list[str] = []
    for value in values:
        for note_id in _ID_RE.findall(value) or _BARE_ID_RE.findall(value):
            if note_id not in out:
                out.append(note_id)
    return tuple(out)


def check_prose(body: str) -> str:
    """A check note's own words — its body with the `# Title` heading removed.

    The prose lives in the BODY, not in frontmatter, and that is the whole
    reason this type is worth having: a person opens `CHK-0412-First-Run.md` in
    Obsidian and reads a sentence, then a procedure. A 2,000-character `text:`
    field would have been the JSON objection ([[FEAT-0112]]) arriving through
    the back door — machine-shaped storage a human cannot comfortably edit.
    """
    lines = (body or "").strip().splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def item_from_note(
    frontmatter: dict[str, Any], *, rel: str = "", body: str = "",
) -> Item | None:
    """One `CHK-*` note as an `Item`, or `None` if it is not one.

    Returns `None` only for a note that is not a check at all. A malformed
    check is **not** dropped: it lands in Tier 1 and blocks.

    That is the same direction the row parser fails in — *"anything the parser
    cannot classify is neither, so it is owed and blocks"* — and getting it
    wrong here is worse than there, because a whole note is at stake rather
    than one character. The first cut returned `None` on an unreadable tier
    under a comment claiming that dropping it kept the gate honest. It does
    not: a dropped check and a Tier 3 check both fail to block, so both let a
    release through on a check nobody can read. **A mutation setting the
    fallback to Tier 3 survived the suite**, which is how the reasoning came to
    be checked rather than admired.
    """
    fm = frontmatter or {}
    if not str(fm.get("id", "") or "").strip():
        return None
    try:
        tier = int(str(fm.get("tier", "")).strip() or 0)
    except (TypeError, ValueError):
        tier = 0
    if tier not in (1, 2, 3):
        tier = 1
    mark = normalise_mark(str(fm.get("mark", " ") or " "))
    # A YAML scalar cannot hold a bare space, so `mark: " "` round-trips as the
    # empty string through some writers. Both mean unwalked; nothing else is
    # normalised, because `[ x]` staying unrecognised is the point of the
    # row parser's own refusal to strip (ISS-0141).
    if mark == "":
        mark = " "
    raw_invalid = fm.get("invalidated_by") or {}
    if isinstance(raw_invalid, dict):
        invalid = Invalidation(
            change=str(raw_invalid.get("change", "") or "").strip(),
            reason=str(raw_invalid.get("reason", "") or "").strip(),
            date=str(raw_invalid.get("date", "") or "").strip(),
            raw=str(raw_invalid.get("raw", "") or "").strip(),
        )
        if invalid.change and not invalid.raw:
            invalid = Invalidation(
                invalid.change, invalid.reason, invalid.date,
                f"{invalid.change}: {invalid.reason}" if invalid.reason
                else invalid.change,
            )
        elif invalid.reason and not invalid.raw:
            invalid = Invalidation(
                invalid.change, invalid.reason, invalid.date, invalid.reason)
    else:
        invalid = split_rerun(str(raw_invalid))
    section = str(fm.get("section", "") or "").strip()
    try:
        ordinal = int(str(fm.get("ordinal", "") or 0))
    except (TypeError, ValueError):
        ordinal = 0
    return Item(
        tier=tier,
        section=section,
        area=str(fm.get("area", "") or "").strip(),
        name=str(fm.get("title", "") or "").strip(),
        text=check_prose(body) or str(fm.get("text", "") or "").strip(),
        checked=mark in _CHECKED_MARKS,
        reconciled=mark in _RECONCILED_MARKS,
        excepted=mark in _EXCEPTED_MARKS,
        failed=mark in _FAILED_MARKS,
        needs_rerun=mark in _RERUN_MARKS,
        question=mark in _QUESTION_MARKS,
        invalidated=invalid,
        mark=mark,
        ordinal=ordinal,
        refs=_wikilink_ids(_as_tuple(fm.get("covers"))),
        heading=f"{section} {fm.get('area', '')}".strip(),
        note_id=str(fm.get("id", "") or "").strip(),
        rel=rel,
        status=str(fm.get("status", "") or "").strip(),
        verdict_date=str(fm.get("verdict_date", "") or "").strip(),
        verdict_reason=str(fm.get("verdict_reason", "") or "").strip(),
        command=str(fm.get("command", "") or "").strip(),
        automation=str(fm.get("automation", "") or "").strip(),
        burden=_as_tuple(fm.get("burden")),
        evidence=_as_tuple(fm.get("evidence")),
        migrated_from=str(fm.get("migrated_from", "") or "").strip(),
    )


def _section_key(section: str) -> tuple[int, ...]:
    """`"1.12"` sorts after `"1.2"`. String order does not, and the suite has
    fourteen sections in tier 1 alone."""
    out: list[int] = []
    for part in (section or "").split("."):
        try:
            out.append(int(part))
        except ValueError:
            out.append(0)
    return tuple(out)


#: A retired check is a record, not an obligation ([[ISS-0265]]).
#:
#: `TESTING.md`: *"Nothing removes a check. A check whose subject is gone goes
#: `retired`."* The note is kept deliberately — its `mark` and `verdict_date`
#: survive as the record that the behaviour was once walked, which is the whole
#: difference between retiring and deleting.
#:
#: **What must NOT survive is the obligation.** `retire_check` has written
#: `status: retired` since [[ISS-0249]] and nothing here ever read it, so a
#: retired check stayed in the tiers, kept its row in the mark facets, and
#: **went on blocking the release**. Measured on `../your-trainer` the moment
#: the first one was retired: `TST-0075`, retired with a reason, still in the
#: `unclear` filter and still in the blocking 104. Retiring did nothing a
#: reader could see, which makes the button worse than absent — it reports
#: success and changes no outcome.
def _is_retired(item: "Item") -> bool:
    return str(getattr(item, "status", "") or "").strip().lower() == "retired"


def sort_items(items: list[Item]) -> list[Item]:
    """Suite order: **tier, then id** ([[ISS-0224]]).

    `section` and `ordinal` are a check's position in `ACCEPTANCE_TESTS.md` —
    a document that exists in no migrated repo. [[ADR-0030]] decision 4 already
    declared that address retired; the fields were kept to order the view, and
    then kept ordering it through two further migrations without anybody
    asking whether they still had to.

    **Measured before removing them, and this is the whole argument: `(tier,
    note_id)` is byte-identical to `(tier, section, ordinal, note_id)` in all
    three repos** — 34, 581 and 56 items, first row to last. Not luck: the
    migration allocated ids in document order, so the id *encodes* the
    position it replaced — and unlike the position, it does not move when
    something above it does.

    A file-shape item has no `note_id`, so it keeps the positional key. That
    branch is permanent: twelve historical tags hold that shape, and a tag is
    immutable.
    """
    return sorted(items, key=lambda i: (
        i.tier, "", 0, i.note_id) if i.note_id else (
        i.tier, _section_key(i.section), i.ordinal, ""))


def load_notes(checks_dir: Path) -> list[Item]:
    """Every acceptance note under ``checks_dir``, in suite order.

    `TST-*` since ADR-0031, `CHK-*` in a repo that has not run the merge
    migration. Never both: the migration renames in place, so a directory
    holding one shape has finished and a directory holding the other has not
    started.

    Reads the directory directly rather than through the index, so the
    migration script and the tests can use it without building one. Live
    surfaces pass an `Index` to :func:`load` instead — 579 YAML parses per page
    render is not a thing to do twice.
    """
    import frontmatter as _fm

    items: list[Item] = []
    paths = sorted(checks_dir.glob("TST-*.md")) or sorted(checks_dir.glob("CHK-*.md"))
    for path in paths:
        try:
            post = _fm.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        item = item_from_note(dict(post.metadata), body=post.content,
                              rel=f"{CHECKS_REL}/{path.name}")
        if item is not None:
            items.append(item)
    return sort_items(items)



def apply_ledger(items: list[Item], docs_root: Path, platform: str) -> list[Item]:
    """Replace each check's verdict with what the platform's ledger says.

    **The join** ([[ADR-0037]]). Before this, an item's verdict came out of its
    own frontmatter, which is a scalar and cannot hold a fact about
    *(check × platform × release)* — so 579 of `../your-trainer`'s 581
    acceptance notes claimed a platform-free result that had in fact been
    earned on Android.

    Three properties, and each one is why this is an overlay rather than a
    rewrite of `item_from_note`:

    * **A repo with no ledger is untouched.** Nine of twelve fleet repos have
      none, and every one of them must keep reading exactly as it did.
      `verdicts()` returns `{}` and this returns its input.
    * **A check with no entry falls to `todo`, not to whatever the note still
      says.** That is [[REQ-0054]] made operational: once a ledger exists, the
      absence of an entry IS the verdict, and a leftover `mark: done` in
      frontmatter must not out-vote it. A migrated repo whose notes have shed
      the field reaches the same place from the other direction.
    * **`excused` and `na` both clear, and only one survives the seal** —
      handled in `ledger.resolve`, not here, so there is one implementation of
      the expiry rather than one per surface.
    """
    from . import ledger as _ledger

    if not _ledger.has_ledger(docs_root):
        return items
    if platform:
        found = _ledger.verdicts(docs_root, platform)
    else:
        #: **No platform named: every platform must clear it** ([[DES-0012]]
        #: D4, [[TASK-0534]]). A release that has not said which platform it
        #: ships takes them all — the same opt-in rule D4 gives release
        #: contents — so a check clears only where every platform with a
        #: ledger says it clears, and the earliest such verdict is reported
        #: because that is the weakest evidence behind the claim.
        #:
        #: Fails closed by construction: a platform that has said nothing has
        #: no entry, so the check is owed and the intersection is empty.
        per = [_ledger.verdicts(docs_root, p)
               for p in _ledger.platforms(docs_root)]
        found = {}
        if per:
            for check in set(per[0]).intersection(*(set(d) for d in per[1:])):
                verdicts = [d[check] for d in per]
                if all(v.clears for v in verdicts):
                    found[check] = min(verdicts, key=lambda v: v.date)
    by_check: dict[str, list[Any]] = {}
    for led in _ledger.load(docs_root, platform):
        for item in led.evidence:
            by_check.setdefault(item.check, []).append(item)
    out: list[Item] = []
    for item in items:
        verdict = found.get(item.note_id)
        mark = verdict.mark if verdict else "todo"
        out.append(replace(
            item,
            mark=mark,
            checked=mark == "pass",
            reconciled=mark == "partial",
            #: BOTH non-gating exceptions land here, because `excepted` is what
            #: `settled` reads and both clear. The difference between them is
            #: not visible at this layer and must not be: it is *when they
            #: expire*, which `ledger.resolve` has already applied.
            excepted=mark in ("na", "excused"),
            failed=mark == "fail",
            question=mark == "question",
            #: `blocked` blocks. It is not `failed` — the behaviour may be
            #: perfectly fine and the rig was down — so it is carried as
            #: neither, which is the state an unrecognised mark has always had
            #: and is the direction that fails safe.
            needs_rerun=False,
            verdict_date=verdict.date if verdict else "",
            verdict_reason=verdict.reason if verdict else "",
            #: [[TASK-0544]]. Evidence follows the verdict it backs, so it is
            #: joined out of the ledger's sibling collection rather than read
            #: from the note — a screenshot proves one walk on one platform on
            #: one date, and on a permanent check that is the standing claim
            #: decision 3 rejects for `automation:`.
            evidence=tuple(
                v.ref for v in by_check.get(item.note_id, ())
                if verdict and v.date == verdict.date
            ),
        ))
    return out


def load(docs_root: Path, index: "Any | None" = None, *,
         platform: str = "") -> Suite:
    """The suite, or an empty one when the repo has never instantiated it.

    **Absent is not passing.** A repo with no suite has no Tier 1/2 items, so
    `blocking()` is empty and the gate would report "clear" — which is exactly
    the state every repo was in before this existed, and exactly the state that
    made the gate look like it worked. `gate_payload` reports `exists` so a
    surface can say "never instantiated" instead of "nothing blocking".

    **Notes win where both exist.** They should never both exist — the
    migration deletes the file in its own commit — but if a stray copy is ever
    restored, reading the notes is the answer that matches every write path.
    The alternative would be a surface that displays one store and writes the
    other.
    """
    checks_dir = docs_root / CHECKS_REL
    if index is not None:
        # ADR-0031: an acceptance check is a `[[test]]` at `level: acceptance`.
        # The retired `check` type is still read, because eight of the twelve
        # repos this cockpit renders are upstream-behind and a repo that has
        # not run the merge migration must keep its suite rather than losing
        # it silently -- which is what reading only the new shape would do.
        records = [
            r for r in index.notes_by_type("test")
            if str(r.frontmatter.get("level", "") or "").strip().lower() == "acceptance"
        ] or list(index.notes_by_type("check"))
        items = [
            item for record in records
            if (item := item_from_note(record.frontmatter, body=record.body,
                                       rel=record.rel_path))
            is not None
        ]
        if items:
            items = apply_ledger(items, docs_root, platform)
            #: Dropped here rather than in each consumer: the gate, the tiers
            #: and the facets all read `Suite.items`, and three filters is how
            #: two of them come to disagree ([[REQ-0059]]).
            items = [i for i in items if not _is_retired(i)]
            return Suite(path=checks_dir, items=sort_items(items),
                         shape=SHAPE_NOTES, platform=platform)
    elif checks_dir.is_dir():
        items = load_notes(checks_dir)
        if items:
            items = apply_ledger(items, docs_root, platform)
            items = [i for i in items if not _is_retired(i)]
            return Suite(path=checks_dir, items=items, shape=SHAPE_NOTES,
                         platform=platform)
    path = docs_root / SUITE_REL
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return Suite()
    return Suite(path=path, items=parse(text), shape=SHAPE_FILE)


# ----- the gate as a delta (FEAT-0108 / TASK-0446) --------------------------
#
# The gate has reported one number since it shipped, and against `your-trainer`
# that number has been *"a release is blocked"* at **all twelve tags**: 1, 15,
# 85, 130, 22, 47, 47, 47, and 60 at HEAD. It is the steady state, not news,
# and today's 60 is not even elevated — v1.1.55 shipped at 130.
#
# A sentence that has been true and ignored twelve times is one the reader has
# learned to skip. What has never been said is which of the sixty arrived since
# the last release, and that is a number a person can act on today.
#
# The baseline needs no new storage: `git show <tag>:docs/tests/…` reconstructs
# the suite exactly as it stood, and `parse` reads it unchanged.


#: Diffed on `Item.name` within tier, never on `Item.number`. Numbers shift
#: when a section is inserted above — the same asymmetry `locate()` relies on,
#: pointing the other way: there it makes a stale address FAIL rather than
#: resolve to the wrong row; here it would make an unchanged row look new.
def _delta_key(item: "Item") -> tuple[int, str]:
    return (item.tier, item.name.strip().casefold())


#: One `git show` + parse per (repo, ref), for the life of the process. A tag's
#: content does not change, and the alternative is 12 subprocesses and 12
#: parses of a 1082-line file **per page render** — the gate is on a page
#: somebody clicks repeatedly. A moved tag goes stale here until restart, which
#: is the right trade for a ref that is by convention immutable.
_at_ref: dict[tuple[str, str], "Suite | None"] = {}


def suite_at(project_root: Path, ref: str, rel: str = SUITE_REL) -> Suite | None:
    """The suite as it stood at ``ref``, or ``None`` if it cannot be read.

    ``None`` is a real answer and is distinct from an empty suite: a tag from
    before the file existed, a ref that does not resolve, and a file that is
    present but empty are three different situations, and only the last one
    means *"the suite had no items then"*.

    **Two shapes, split by TIME rather than maintained in parallel**
    (TASK-0462). Every ref before a repo's migration commit holds the file —
    that is all twelve of `../your-trainer`'s current tags, so the delta at
    every historical tag is computed by exactly the code that always computed
    it. Refs after the cut hold notes, and are read with **two** subprocesses
    rather than N: `git ls-tree` for the paths, `git cat-file --batch` for
    their contents in one stream. The branch is permanent and that is not a
    defect — a tag is immutable, so the shape a tag holds is a fact about the
    past that will never stop being true.
    """
    cache_key = (str(project_root), f"{ref}:{rel}")
    if cache_key in _at_ref:
        return _at_ref[cache_key]
    out = _suite_at_uncached(project_root, ref, rel)
    _at_ref[cache_key] = out
    return out


def _suite_at_uncached(project_root: Path, ref: str, rel: str) -> Suite | None:
    from .git_state import _git_raw

    text = _git_raw(project_root, "show", f"{ref}:docs/{rel}")
    if text is not None:
        return Suite(path=None, items=parse(text), shape=SHAPE_FILE)
    if rel != SUITE_REL:
        # An explicit non-default path was asked for and is not there. Answering
        # with the note shape would be answering a different question.
        return None
    items = _notes_at(project_root, ref)
    if items is None:
        return None
    #: **The third shape** ([[TASK-0545]]). Refs before the document migration
    #: hold `ACCEPTANCE_TESTS.md`; refs after it hold notes carrying their own
    #: `mark:`; refs after [[ADR-0037]] hold notes carrying NOTHING, with the
    #: verdict in a ledger beside them. Reading only the notes at such a ref
    #: would report every tag as zero-walked — and that is the one failure mode
    #: here that produces a WRONG ANSWER rather than an error, because a
    #: historical suite with no verdicts looks exactly like a historical suite
    #: nobody walked.
    #:
    #: A tag is immutable, so the shape a tag holds is a permanent fact about
    #: the past and this branch never goes away.
    at_ref = _ledger_at(project_root, ref)
    if at_ref:
        from . import ledger as _ledger
        found = _ledger.resolve(at_ref)
        items = [
            replace(i,
                    mark=(v.mark if (v := found.get(i.note_id)) else "todo"),
                    checked=bool(v) and v.mark == "pass",
                    reconciled=bool(v) and v.mark == "partial",
                    excepted=bool(v) and v.mark in ("na", "excused"),
                    failed=bool(v) and v.mark == "fail",
                    question=bool(v) and v.mark == "question",
                    needs_rerun=False,
                    verdict_date=v.date if v else "",
                    verdict_reason=v.reason if v else "")
            for i in items
        ]
    return Suite(path=None, items=items, shape=SHAPE_NOTES)


def _ledger_at(project_root: Path, ref: str) -> list["Any"]:
    """Every ledger at ``ref``, oldest first — the same two subprocesses.

    Returns `[]` when the ref predates the ledger, which is not an error: it is
    the second of the three shapes, and its verdicts are on the notes.
    """
    import json
    import subprocess

    from . import ledger as _ledger
    from .git_state import _git_raw

    listing = _git_raw(project_root, "ls-tree", "-r", "-z", ref,
                       f"docs/{_ledger.LEDGERS_REL}/")
    if not listing:
        return []
    shas, names = [], []
    for entry in listing.split("\0"):
        if not entry.strip():
            continue
        meta, _, path = entry.partition("\t")
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob" or not path.endswith(".json"):
            continue
        shas.append(parts[2])
        names.append(path.rsplit("/", 1)[-1])
    if not shas:
        return []
    try:
        blob = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=str(project_root),
            input="\n".join(shas).encode(), capture_output=True, check=False)
    except OSError:                                      # pragma: no cover
        return []
    out = []
    for name, body in zip(names, _split_batch(blob.stdout)):
        try:
            raw = json.loads(body)
        except ValueError:                               # pragma: no cover
            continue
        found = _ledger._LEDGER_NAME_RE.match(name[:-5])
        if not found:
            continue
        try:
            led = _ledger._parse(body, where=name,
                                 platform=found.group("platform"))
        except _ledger.LedgerError:
            #: A historical ledger this reader cannot parse is skipped rather
            #: than raised: the past is immutable, so refusing it would make a
            #: surface unable to render a tag nobody can fix.
            continue
        out.append(led)
    out.sort(key=lambda l: (l.is_working, l.sealed))
    return out


def _notes_at(project_root: Path, ref: str) -> list[Item] | None:
    """Every `CHK-*` note at ``ref``, or ``None`` when the directory is absent.

    Two subprocesses regardless of how many checks there are. `ls-tree` names
    the blobs; `cat-file --batch` streams all of them through one pipe, which
    is the difference between 2 processes and 579 at every tag on a cold delta.
    """
    import subprocess

    from .git_state import _git_raw

    listing = _git_raw(project_root, "ls-tree", "-r", "-z", ref, f"docs/{CHECKS_REL}/")
    if not listing:
        return None
    shas: list[str] = []
    for entry in listing.split("\0"):
        if not entry.strip():
            continue
        # `<mode> <type> <sha>\t<path>`
        meta, _, path = entry.partition("\t")
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            continue
        name = path.rsplit("/", 1)[-1]
        #: **`TST-` and `CHK-`.** This read `CHK-` alone and never followed
        #: [[ADR-0031]]'s renumber, so from the merge onward it matched
        #: nothing: `_notes_at` returned `None`, `suite_at` returned `None`,
        #: and the release delta reported *"not comparable"* at every
        #: post-migration ref — including HEAD. Silent, and in the direction
        #: that makes a surface say less rather than something wrong, which is
        #: why it survived two migrations. Found 2026-08-19 ([[ISS-0221]]).
        if not (name.startswith(("TST-", "CHK-")) and name.endswith(".md")):
            continue
        shas.append(parts[2])
    if not shas:
        return None
    try:
        done = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=str(project_root), input=("\n".join(shas) + "\n").encode(),
            capture_output=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):     # pragma: no cover
        return None
    if done.returncode != 0:
        return None                                  # pragma: no cover
    items: list[Item] = []
    for blob in _split_batch(done.stdout):
        item = _item_from_note_text(blob)
        if item is not None:
            items.append(item)
    return sort_items(items) if items else None


def _split_batch(stream: bytes) -> list[str]:
    """`git cat-file --batch` output as a list of blob bodies.

    The format is `<sha> <type> <size>\\n<contents>\\n` per object, and the
    **size is authoritative** — a note whose body happens to contain a line
    looking like a header would otherwise split an object in two, and half a
    frontmatter block parses as a check with no tier.

    **`size` is in BYTES, so this walks bytes.** The first version took the
    same slices out of a *decoded string*, which is the same thing only for
    pure ASCII. Measured on `../your-trainer` the hour it migrated: 503,860
    bytes of notes decoding to 501,153 characters, so the walk drifted by one
    position per non-ASCII byte — em-dashes, `✅`, the arrows in the prose —
    reached a header it could not parse, and stopped. It returned **314 of
    579 checks, with no error**, and the gate at every post-migration ref
    would have read 20 blocking where the truth is 60: the direction that
    lets a release through.

    The docstring above was already right and the code did not follow it.
    Found by measuring the delta at real tags, not by reading it.
    """
    out: list[str] = []
    pos = 0
    while pos < len(stream):
        newline = stream.find(b"\n", pos)
        if newline == -1:
            break
        header = stream[pos:newline].split()
        if len(header) != 3 or not header[2].isdigit():
            break                                    # pragma: no cover
        size = int(header[2])
        start = newline + 1
        out.append(stream[start:start + size].decode("utf-8", "replace"))
        pos = start + size + 1                       # the trailing newline
    return out


def _item_from_note_text(text: str) -> Item | None:
    import frontmatter as _fm

    try:
        post = _fm.loads(text)
    except (ValueError, UnicodeDecodeError):         # pragma: no cover
        return None
    return item_from_note(dict(post.metadata), body=post.content)


def ages(
    project_root: Path, items: list["Item"], tags: list[str],
) -> dict[str, str]:
    """For each chronic row, the oldest tag at which it was already unsettled.

    ``tags`` oldest-first. The answer is *"this has been open since here"*,
    which is what turns 47 into *"25 since v2.0.5, 14 since v2.0.0, one since
    v1.1.0"* — the difference between a backlog and a five-month-old one.

    A row absent from every tag gets no entry rather than a wrong one. Rows are
    keyed by `Item.key`, so the caller can look one up without re-diffing.
    """
    if not tags:
        return {}
    snapshots: list[tuple[str, set[tuple[int, str]]]] = []
    for tag in tags:
        suite = suite_at(project_root, tag)
        if suite is None:
            continue
        snapshots.append((tag, {
            _delta_key(i) for i in suite.items
            if section_of(i) in MANUAL_SECTIONS and not i.settled
        }))
    out: dict[str, str] = {}
    for item in items:
        key = _delta_key(item)
        for tag, unsettled in snapshots:     # oldest first — first hit wins
            if key in unsettled:
                out[item.key] = tag
                break
    return out


def delta(current: Suite, baseline: Suite | None) -> dict[str, Any]:
    """Today's blocking rows split into new / chronic / regressed.

    ``baseline`` of ``None`` — no tags, no previous release, the file absent at
    the tag — yields every blocking row as ``chronic`` with ``comparable``
    false, so a caller renders the census it rendered before rather than
    claiming everything is new. **That is the common case**: eleven of the
    twelve repos the cockpit discovers have no release tags at all.
    """
    blocking = current.blocking()
    if baseline is None:
        return {
            "comparable": False,
            "new": [], "chronic": list(blocking), "regressed": [],
        }
    was_settled = {
        _delta_key(i) for i in baseline.items
        if section_of(i) in MANUAL_SECTIONS and i.settled
    }
    was_present = {
        _delta_key(i) for i in baseline.items if section_of(i) in MANUAL_SECTIONS
    }
    new, chronic, regressed = [], [], []
    for item in blocking:
        key = _delta_key(item)
        if key not in was_present:
            new.append(item)
        elif key in was_settled:
            regressed.append(item)
        else:
            chronic.append(item)
    return {
        "comparable": True,
        "new": new, "chronic": chronic, "regressed": regressed,
    }


def suite_rel(suite: Suite) -> str:
    """What a surface should open to SEE this suite.

    The file, when the file is the suite. The generated view, when the notes
    are — because in note shape there is no document to open, and a link to a
    directory is a 404 dressed as a row.
    """
    if not suite.exists:
        return ""
    return CHECKS_REL if suite.shape == SHAPE_NOTES else SUITE_REL


#: How each tier reads on the view. The template's own words; TESTING.md is the
#: contract and this must not paraphrase it into a second one.
#: **The three sections, derived and never filed** ([[ADR-0039]]).
#:
#: `tier:` was a fourth axis restating part of a field [[ADR-0034]] had already
#: made authoritative: `covers:` says what a check is about, `command:` says who
#: executes it, and between them they answer everything the tier answered.
#:
#: The order below IS the precedence and it is deliberate. `command:` wins,
#: because Edwin's question is *does a machine do this* and there is one answer
#: — an automated regression check is an automated test, and it does not matter
#: why it was automated.
SECTION_AUTOMATED = "automated"
SECTION_REGRESSION = "regression"
SECTION_FEATURE = "feature"

#: Sections in display order. Feature tests first: they are the standing claims
#: about behaviour and the largest population (405 of 671 fleet-wide).
SECTION_ORDER: tuple[str, ...] = (
    SECTION_FEATURE, SECTION_REGRESSION, SECTION_AUTOMATED,
)

SECTION_LABELS: dict[str, str] = {
    SECTION_FEATURE: "Feature tests",
    SECTION_REGRESSION: "Regression tests",
    SECTION_AUTOMATED: "Automated tests",
}

#: Sections a person is asked to complete. **This replaces `GATING_TIERS`**,
#: and it is one rule where there were two constants and a tier test: an
#: unsettled manual check blocks, an automated one never enters the list.
MANUAL_SECTIONS: frozenset[str] = frozenset({SECTION_FEATURE, SECTION_REGRESSION})

_ISS_REF = re.compile(r"\bISS-\d+")

#: The older document shape's three headings, in the order `TESTING.md` has
#: always listed them. Tier 3 maps to the automated section because that is
#: what Tier 3 had become -- 67 of `your-trainer`'s 68 arrived there through
#: the *Unit test replacement* rule -- and because it preserves the one
#: behaviour that matters for an unmigrated repo: Tier 3 never gated.
_FILE_SHAPE_SECTIONS: dict[int, str] = {
    1: SECTION_FEATURE, 2: SECTION_REGRESSION, 3: SECTION_AUTOMATED,
}


def section_of(item: "Item") -> str:
    """Which section a check belongs to. Computed; nothing files a check here.

    A check asserting *the system does X* is a standing claim about behaviour
    and a later change can falsify it. A check asserting *this defect was
    fixed* is a claim about a past event, and nothing a later change does can
    falsify it -- so *never re-checked* is a property of what the check
    asserts rather than a policy applied to it. That is why this is derivable
    at all, and it is [[ADR-0039]] decision 4.

    **A check that names no `ISS-*` reads as a behaviour claim**, which is the
    safe direction: it stays on the list rather than silently settling
    forever. Measured 2026-08-19, 68 of `your-trainer`'s 164 regression checks
    name none anywhere in the note, which is why [[REQ-0060]] makes the link an
    authoring rule and grandfathers those by id.
    """
    #: **File shape reads its heading, because that is where its section was
    #: authored.** A row parsed out of `ACCEPTANCE_TESTS.md` has no `command:`
    #: and no frontmatter `covers:` -- a document cannot carry either -- so the
    #: derivation has nothing to read and would classify all three of its
    #: headings as feature tests. That would put a document's Tier 3 rows into
    #: the gate for the first time, which is a change to what shipping means,
    #: arrived at by accident, in the repos that have not migrated.
    #:
    #: `TESTING.md` still describes both shapes, and for the older one the
    #: heading IS the authored section. The derivation is for notes, which is
    #: where the two fields exist.
    if not item.note_id:
        return _FILE_SHAPE_SECTIONS.get(item.tier, SECTION_FEATURE)
    if item.command:
        return SECTION_AUTOMATED
    if any(_ISS_REF.match(ref) for ref in item.refs):
        return SECTION_REGRESSION
    return SECTION_FEATURE


def section_label(section: str) -> str:
    return SECTION_LABELS.get(section, section)


def view_payload(docs_root: Path, index: "Any | None" = None, *,
                 platform: str = "") -> dict[str, Any]:
    """The suite as a **list somebody walks** (FEAT-0114 / TASK-0464).

    Edwin's contract, verbatim: *"We can then present them still as the same
    list with the same tick options for me to go through before a release."* So
    the shape is the shape a reader already knows — tier, then area, then rows
    in order — and the marks are the same six.

    What changes is where it comes from. The document was the display, which is
    why four rounds of work (ISS-0185..0189) went into teaching a rendered
    Markdown file to behave like a control surface. This is a projection over
    frontmatter, like every other view in the cockpit.

    **The facets are derived, never authored.** Every filter here is a field —
    mark, tier, area, `covers:`, `automation:` — which is the concrete thing
    the migration bought: the old suite could only be filtered by whatever a
    section heading happened to say, and `missing_issue_refs` reported 158 of
    158 because it could not read the form the headings were written in.
    """
    suite = load(docs_root, index, platform=platform)
    tiers: list[dict[str, Any]] = []
    #: **Sections, derived** ([[ADR-0039]]). This loop read `tier:` and
    #: rendered `Tier 1 — feature tests`; it now asks `section_of` and renders
    #: the same three names without a field selecting them. A check that gains
    #: a `command:` moves here with no other edit, and one whose command stops
    #: resolving moves back — which is the property a filed section could not
    #: have, and the reason 67 of `your-trainer`'s 68 Tier 3 checks were still
    #: reading a heading from a document that had been deleted.
    by_section: dict[str, list[Item]] = {}
    for item in suite.items:
        by_section.setdefault(section_of(item), []).append(item)
    for name in SECTION_ORDER:
        items = by_section.get(name) or []
        if not items:
            continue
        areas: list[dict[str, Any]] = []
        for item in items:
            #: **`area` alone** ([[ISS-0224]]). Measured 2026-08-19: areas
            #: spanning more than one section — **0** in all three repos
            #: (21/21, 77/77, 20/20), so `section` added nothing to the key
            #: and only a second thing to keep in step.
            key = item.area
            if not areas or areas[-1]["area"] != key:
                areas.append({
                    "section": item.section, "area": item.area,
                    "refs": list(item.refs), "items": [],
                })
            areas[-1]["items"].append(_row(item))
        #: **Incomplete rows to the top of their own section** ([[TASK-0556]]).
        #:
        #: Edwin scoped this deliberately: the area order and the tier order do
        #: not move, because this page is where the suite is WALKED and a list
        #: that reorders itself as you tick things is one you lose your place
        #: in. Inside a section, what is owed is at the top.
        #:
        #: Stale counts as incomplete — the same predicate the percentage on
        #: the heading uses, so a section's number and its order cannot
        #: disagree.
        for area in areas:
            area["items"].sort(key=lambda r: (
                bool(r.get("checked") or r.get("reconciled")
                     or r.get("excepted")) and not r.get("stale"),
                str(r.get("id") or r.get("number") or ""),
            ))
        #: **An automated section carries no checkbox and no todo count.**
        #: A tickbox beside something no person executes is what put nine
        #: automated checks into `your-trainer`'s blocking 68 ([[ISS-0237]]).
        manual = name in MANUAL_SECTIONS
        tiers.append({
            "section_key": name,
            "label": section_label(name),
            # Kept so a client pinned to the old payload keeps rendering. The
            # value is the section's position, not a `tier:` read from a note:
            # nothing writes one any more.
            "tier": SECTION_ORDER.index(name) + 1,
            "manual": manual,
            "gating": manual,
            "total": len(items),
            "checked": sum(1 for i in items if i.checked),
            "reconciled": sum(1 for i in items if i.reconciled),
            "excepted": sum(1 for i in items if i.excepted),
            "unsettled": sum(1 for i in items if manual and not i.settled),
            "stale": sum(1 for i in items if i.stale),
            "areas": areas,
        })
    return {
        "exists": suite.exists,
        "shape": suite.shape,
        #: **Which platform these verdicts are about** ([[ADR-0037]]). A
        #: surface that renders a verdict without naming its platform is the
        #: defect this decision exists to remove: 579 acceptance notes recorded
        #: an Android result as a fact about the app. Empty means the union —
        #: every platform must clear a check for it to read as cleared.
        "platform": suite.platform,
        "rel": suite_rel(suite),
        # The rules preamble, as a row rather than as re-rendered prose: the
        # README holds it verbatim and is one click away. Re-rendering it into
        # the header would make this view a second publisher of the document's
        # own words, which is the drift the migration exists to remove.
        "readme": (f"{CHECKS_REL}/README.md"
                   if suite.shape == SHAPE_NOTES else suite_rel(suite)),
        "tiers": tiers,
        "facets": _facets(suite),
        "blocking": len(suite.blocking()),
        "total": len(suite.items),
        "settled": sum(1 for i in suite.items if i.settled),
    }


def _facets(suite: Suite) -> dict[str, list[dict[str, Any]]]:
    """Every filter the view offers, with its count, derived from the fields.

    A facet with a zero count is omitted rather than shown greyed: a filter
    that can only ever return nothing is a control that wastes a click, and on
    a 579-row suite there would be a dozen of them.
    """
    def tally(values: "list[tuple[str, str]]") -> list[dict[str, Any]]:
        counts: dict[tuple[str, str], int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        return [
            {"value": value, "label": label, "count": count}
            for (value, label), count in sorted(
                counts.items(), key=lambda kv: (-kv[1], kv[0][1]))
        ]

    marks: list[tuple[str, str]] = []
    for item in suite.items:
        marks.append((item.mark, MARK_MEANING.get(item.mark, "unrecognised")))
    return {
        "marks": tally(marks),
        # The facet is the SECTION now, under the key `tiers` so a pinned
        # client keeps working. Nothing here reads `tier:`.
        "tiers": tally([(section_of(i), section_label(section_of(i)))
                        for i in suite.items]),
        "areas": tally([(i.area, i.area) for i in suite.items if i.area]),
        "covers": tally([(ref, ref) for i in suite.items for ref in i.refs]),
        "automation": tally([(i.automation, i.automation)
                             for i in suite.items if i.automation]),
    }


#: What each mark MEANS, in one word a filter chip can carry. The table in the
#: module docstring above is the long form; this is the label, and the two are
#: kept beside each other deliberately — a vocabulary explained in one place
#: and displayed from another is how `[!]` came to mean two things.
#: **Keyed on the WORD**, because `normalise_mark` translates on read and every
#: item reaching a surface already carries one (ADR-0034 / ISS-0200). This was
#: keyed on the characters after the vocabulary migrated, so the live filter bar
#: read *"unrecognised · 33"* in all three suites — the model migrated and the
#: surfaces did not. The characters stay as aliases for a payload built without
#: normalisation.
MARK_MEANING: dict[str, str] = {
    #: **The ledger's vocabulary** ([[ADR-0037]]), which is what a migrated
    #: repo's items carry. `na` and `excused` both clear and are named apart,
    #: because the difference — whether the exception comes back — is the one
    #: a reader most needs and the one no single word for both could carry.
    "pass": "passed", "partial": "partial", "na": "not applicable",
    "excused": "excused this release", "blocked": "could not run",
    "fail": "failed",
    #: The pre-ledger words. Read forever, written nowhere.
    "todo": "todo", "done": "passed", "incomplete": "partial",
    "canceled": "canceled", "important": "failed", "question": "unclear",
    "rerun": "needs re-check",
    # legacy characters, for any path that reaches here un-normalised
    " ": "todo", "x": "passed", "X": "passed",
    "/": "partial", "~": "partial", "-": "canceled",
    "!": "failed", "F": "failed", "?": "unclear",
}


def payload(docs_root: Path, index: "Any | None" = None, *,
            platform: str = "") -> dict[str, Any]:
    """The suite as data, for the Tests view's tier groups."""
    suite = load(docs_root, index, platform=platform)
    return {
        "exists": suite.exists,
        "shape": suite.shape,
        #: **Which platform these verdicts are about** ([[ADR-0037]]). Empty
        #: means the union: every platform must clear a check for it to read
        #: as cleared, which is how a release that has not said what it ships
        #: fails closed.
        "platform": suite.platform,
        "rel": suite_rel(suite),
        "tiers": [
            {
                "tier": SECTION_ORDER.index(n) + 1,
                "section_key": n,
                "label": section_label(n),
                "total": len(suite.section(n)),
                "checked": sum(1 for i in suite.section(n) if i.checked),
                # Reported beside `checked` rather than folded into it: the two
                # are different claims, and a suite that showed 27/27 for 26
                # walked and 1 reconciled would be the drop this replaced,
                # rounded up instead of down (ISS-0141).
                "reconciled": sum(1 for i in suite.section(n) if i.reconciled),
                "excepted": sum(1 for i in suite.section(n) if i.excepted),
                "gating": n in MANUAL_SECTIONS,
                "manual": n in MANUAL_SECTIONS,
                "items": [
                    {
                        "key": i.key, "number": i.number,
                        "section": i.section, "area": i.area,
                        "name": i.name, "text": i.text, "checked": i.checked,
                        "reconciled": i.reconciled,
                        "excepted": i.excepted,
                        "refs": list(i.refs),
                        # The note's own id and path, so a row can BE the
                        # check rather than a position in a document. Empty in
                        # file shape, which is how a caller tells which
                        # address it may trust.
                        "id": i.note_id, "rel": i.rel,
                        "mark": i.mark, "automation": i.automation,
                        "stale": i.stale,
                    }
                    for i in suite.section(n)
                ],
            }
            for n in SECTION_ORDER
        ],
    }


def _releases_since(tag: str, tags: list[str]) -> int:
    """How many tags were cut after ``tag``. ``tags`` oldest-first.

    ``0`` when the tag is unknown — never a guess, and never the total, which
    would report a row nobody can date as the oldest debt in the project.
    """
    if not tag or tag not in tags:
        return 0
    return len(tags) - tags.index(tag) - 1


def _summary(tags: list[str], suites: dict[str, int], today: int) -> str:
    """The one line that lets a reader judge whether today is unusual.

    *"Twelve releases, median 26 blocking at ship. This is 60."* Without it,
    60 is a number with nothing to compare against — which is exactly how it
    came to be ignored twelve times. Computed, never written down, so it
    cannot drift from the tags it describes.
    """
    counts = sorted(suites[t] for t in tags if t in suites)
    if not counts:
        return ""
    middle = len(counts) // 2
    median = (counts[middle] if len(counts) % 2
              else (counts[middle - 1] + counts[middle]) // 2)
    return (f"{len(counts)} release{'s' if len(counts) != 1 else ''}, "
            f"median {median} blocking at ship. This is {today}.")


def _row(item: "Item", **extra: Any) -> dict[str, Any]:
    """One gate row. Every group emits this shape, so the client has one
    renderer rather than four that drift."""
    out: dict[str, Any] = {
        "tier": item.tier, "number": item.number, "section": item.section,
        "area": item.area, "name": item.name, "refs": list(item.refs),
        # The check's own words and its own address (FEAT-0103). Without these
        # the gate could only ever say how MANY, which is what Edwin reported
        # after the count shipped: *"I still don't seem to be able to see and
        # execute the current set."*
        "text": item.text, "anchor": item.anchor,
        "failed": item.failed, "rerun": item.rerun,
        # The note shape's address (ADR-0030). `number` still ships beside it
        # and still shifts; `id` does not, which is what every write path
        # prefers once a repo has migrated. Empty on a file-shape row, so a
        # client can tell which address it may trust without being told.
        "id": item.note_id, "rel": item.rel,
        "verdict_date": item.verdict_date,
        "verdict_reason": item.verdict_reason,
        "automation": item.automation,
        # **What executes it, so the row can say so instead of drawing a
        # checkbox** (ADR-0039). The client cannot tell an automated check
        # from a manual one without this -- which is ISS-0237 exactly, one
        # layer up from `item_from_note` not reading the field at all.
        "command": item.command,
        "invalidated_by": {
            "change": item.invalidated.change,
            "reason": item.invalidated.reason,
            "date": item.invalidated.date,
        } if item.invalidated else {},
        "stale": item.stale,
        # The mark the file holds, so the row can DRAW it (ISS-0190). The gate
        # row and the document row are the same check and now wear the same
        # control; one of them reading its state from `data-mark` and the other
        # inferring it from booleans is how the two would come to disagree.
        "mark": item.mark,
    }
    out.update(extra)
    return out


def gate_payload(
    docs_root: Path,
    index: "Any | None" = None,
    project_root: Path | None = None,
    baseline_ref: str = "",
    tags: "list[str] | None" = None,
    platform: str = "",
    deselected: "set[str] | None" = None,
) -> dict[str, Any]:
    """What blocks a release, in the template's own terms.

    The wording is the contract's, not this module's: *"A release is blocked
    while any Tier 1/Tier 2 test is unchecked (exceptions must be documented in
    the release note)."* A surface that paraphrased it would be a second
    statement of the rule, and the two would drift.

    **`blocking` keeps its old meaning and its old membership.** Every argument
    after `docs_root` is optional and additive: without them this returns what
    it always returned, which is what keeps the Tests view and every existing
    caller working while the Publication page asks for more.
    """
    suite = load(docs_root, index, platform=platform)
    #: **Selection SUBTRACTS** ([[ADR-0040]] via [[TASK-0512]]). `deselected`
    #: is the features a release has held back; empty or `None` means nothing
    #: was, and this is exactly `blocking()`. Eleven historical releases depend
    #: on that being true.
    unsubtracted = suite.blocking()
    blocking = suite.blocking_minus(deselected)

    # --- quiet: the subject is not in flight (TASK-0447) ------------------
    #
    # ADR-0028 decision 3, finally reaching the population the ADR was written
    # about. Measured on `your-trainer`: 20 of the 60 are section 1.25, whose
    # FEAT-0074 is `backlog` — checks describing a screen that does not exist.
    quiet_rows: list[dict[str, Any]] = []
    resting_rows: list[dict[str, Any]] = []
    live: list[Item] = list(blocking)
    if index is not None:
        from . import obligations

        quiet = [i for i in blocking
                 if obligations.ids_are_unbuilt(i.refs, index)]
        quiet_keys = {i.key for i in quiet}
        live = [i for i in blocking if i.key not in quiet_keys]
        quiet_rows = [
            _row(i, subjects=obligations.resting_reason(i.refs, index))
            for i in quiet
        ]

        #: **A regression guard rests with its issue** ([[TASK-0526]]).
        #: Edwin: *"there should be very few tier-2 items active at any given
        #: time, so should not overwhelm."*
        #:
        #: The mirror of `quiet` at the other end of a subject's life: that
        #: rests a check whose subject is not built, this rests one whose issue
        #: is CLOSED. The check is kept and simply not asked about — and it
        #: wakes on its own if the issue reopens, which is the case a
        #: retirement rule could not express.
        #:
        #: **REGRESSION ONLY, and this restriction is the whole safety of it.**
        #: A feature check whose `FEAT-*` is `done` is the ordinary state of
        #: every settled feature in the repo; resting on that would empty the
        #: gate. A regression check's subject is the DEFECT it guards, and a
        #: closed defect is exactly the condition under which nobody needs to
        #: re-walk it. Measured on `your-trainer` 2026-08-20 (working tree):
        #: 14 of the 59 blocking are regression checks and **11** have all
        #: their issues closed, so the gate reads 48 rather than 59 -- and the
        #: 11 are listed, counted and one click away, never silently gone.
        resting = [
            i for i in live
            if section_of(i) == SECTION_REGRESSION
            and obligations.ids_are_settled(i.refs, index)
        ]
        resting_keys = {i.key for i in resting}
        live = [i for i in live if i.key not in resting_keys]
        resting_rows = [
            _row(i, subjects=obligations.resting_reason(i.refs, index))
            for i in resting
        ]

    # --- stale: ticked, but the row says the evidence no longer holds -----
    stale = [i for i in suite.items if section_of(i) in MANUAL_SECTIONS and i.stale]

    # --- the delta (TASK-0446) --------------------------------------------
    baseline = (
        suite_at(project_root, baseline_ref)
        if project_root is not None and baseline_ref else None
    )
    split = delta(suite, baseline)
    live_keys = {i.key for i in live}
    # The delta is computed over ALL blocking rows and then intersected with
    # the live ones, rather than over `live` directly. A quiet row is still
    # new or chronic — it is just not being asked about — and computing the
    # split on the filtered set would make the numbers depend on the order the
    # two rules were applied.
    groups = {
        name: [i for i in split[name] if i.key in live_keys]
        for name in ("new", "chronic", "regressed")
    }
    age_by_key = (
        ages(project_root, groups["chronic"], tags or [])
        if project_root is not None and tags else {}
    )
    # The historical line. Every tag is already parsed and cached by `ages`,
    # so this costs a dict comprehension rather than a second walk.
    history: dict[str, int] = {}
    if project_root is not None and tags:
        for tag in tags:
            at = suite_at(project_root, tag)
            if at is not None:
                history[tag] = len(at.blocking())

    return {
        "exists": suite.exists,
        "shape": suite.shape,
        #: **Which platform these verdicts are about** ([[ADR-0037]]). Empty
        #: means the union: every platform must clear a check for it to read
        #: as cleared, which is how a release that has not said what it ships
        #: fails closed.
        "platform": suite.platform,
        "rel": suite_rel(suite),
        "blocked": bool(blocking),
        #: **What the selection cost** ([[TASK-0576]], [[FEAT-0142]] criterion
        #: 4). A gate that fell from 59 to 23 because somebody held six
        #: features back, rendered as *"23 blocking"* with nothing beside it,
        #: is [[ISS-0241]] and [[ISS-0243]] in a new place: a number with no
        #: recorded cause. `checks` is the SIZE of the subtraction, measured
        #: against the same suite -- never a second count of it.
        "deselection": {
            "features": len(deselected or ()),
            "checks": len(unsubtracted) - len(blocking),
        },
        "rule": "A release is blocked while any manual check is unsettled "
                "(exceptions must be documented in the release note).",
        # The contract's sentence is quoted verbatim above and must stay that
        # way — a paraphrase becomes a second statement of the rule and the two
        # drift. But this repo now clears a check by a second mechanism the
        # contract does not name, and a gate that quotes one rule while
        # implementing another is that same drift wearing the quote as cover.
        # So the extension is stated beside it rather than folded into it, and
        # `TESTING.md` is owed the change upstream (ISS-0141). Found by
        # independent review.
        "local_rule": "This repo also settles a check by reconciliation — a "
                      "`- [~]` mark, meaning the check was closed by a "
                      "decision recorded on its own line rather than by being "
                      "completed. Reconciled checks do not block and are counted "
                      "separately; they are not release exceptions.",
        "blocking": [_row(i) for i in blocking],
        # --- the delta, additive to `blocking` above ----------------------
        #
        # `comparable` false means there was no baseline to diff against —
        # eleven of the twelve repos the cockpit discovers have no release tag
        # at all. The client renders the census it always rendered and says
        # why, rather than calling 60 rows "new".
        "delta": {
            "comparable": bool(split["comparable"]),
            "baseline": baseline_ref if split["comparable"] else "",
            "new": [_row(i) for i in groups["new"]],
            "chronic": [
                _row(i, since=age_by_key.get(i.key, ""),
                     # Not decoration. "Open since v2.0.5" is a fact; "open
                     # since v2.0.5, and you have shipped four releases over
                     # it" is the sentence that makes it a decision.
                     releases_since=_releases_since(
                         age_by_key.get(i.key, ""), tags or []))
                for i in groups["chronic"]
            ],
            "regressed": [_row(i) for i in groups["regressed"]],
            "summary": _summary(tags or [], history, len(blocking)),
        },
        # Quiet rows carry the reason, per ADR-0028 decision 5 — a collapsed
        # group that cannot name its subject is indistinguishable from one
        # that lost the row.
        "quiet": quiet_rows,
        # **Resting with its issue** (TASK-0526). A regression guard whose
        # every `ISS-*` is closed: kept, counted, listed, not owed — and it
        # wakes on its own the moment the issue reopens. Separate from `quiet`
        # because the two rest for opposite reasons (subject not built vs
        # subject finished) and folding them would lose which.
        "resting": resting_rows,
        # Neither blocking nor satisfied. 53 of `your-trainer`'s ticked rows
        # are here, which is why its honest blocking number is 113 and its
        # reported one is 60. Whether these should BLOCK is a change to what
        # shipping means and is deliberately not decided by a payload.
        "stale": [_row(i) for i in stale],
        # Keyed `tier1`/`tier2` so a pinned client keeps reading, but the
        # population is the manual SECTIONS -- feature checks then regression
        # checks. An automated section has no entry here at all, because it is
        # not something a person is asked to complete (ADR-0039).
        "counts": {
            f"tier{i + 1}": {
                "section_key": name,
                "label": section_label(name),
                "total": len(suite.section(name)),
                "unchecked": sum(1 for x in suite.section(name) if not x.settled),
                "reconciled": sum(1 for x in suite.section(name) if x.reconciled),
                "excepted": sum(1 for x in suite.section(name) if x.excepted),
            }
            for i, name in enumerate(
                n for n in SECTION_ORDER if n in MANUAL_SECTIONS)
        },
    }


# ----- addressing a check ---------------------------------------------------
#
# **A check is addressed by its id.** `locate()` and `rewrite_check()` lived
# here and wrote row grammar into `ACCEPTANCE_TESTS.md` by section-and-ordinal,
# because that was the only address a line in a document had. Deleted with the
# document surface (ISS-0192): every write now targets a `CHK-*` note's
# frontmatter, and `CHK-0412` survives an edit anywhere else in the corpus,
# which is what the whole migration bought.
#
# `parse()` above is NOT part of that and stays forever: `suite_at` reads the
# file shape at every pre-migration ref, which is all twelve of
# `../your-trainer`'s tags, and the release-gate delta depends on it.


# ----- the marks the record already uses (FEAT-0111 / TASK-0455) ------------
#
# ISS-0181 items 1 and 2 read as a design problem — no way to mark a check
# intentionally left open, no way to attach text. Both already exist, in
# `../your-trainer`'s own suites, used consistently with a grammar:
#
#     - [F] **Per-rider collapse persistence:** … **FAILS 2026-06-07** —
#       collapse state is stored globally … Tracked as [[ISS-0285]] …
#     - [~] **AI Workout Builder … :** … **Partial pass 2026-06-06**: English
#       prompts come back in English … (see [[ISS-0277]] …)
#     - [x] **[BOTH]** **ISS-0343 HRM reconnects …** ✅ (Claude, tablet:
#       address rotated 7F:D5:… → 73:DD:…; reconnected by name-match)
#
# This repo invented `[!]` for the same purpose in a form no suite writes, and
# shipped its permissive half without the half that asks for a reason
# (ISS-0177). Nothing here needed designing; the vocabulary was invented in
# the wrong place.

#: What a control may write, and what each writes. `[!]` is deliberately
#: absent: it stays READABLE (`_EXCEPTED_MARKS`) so a suite already using it
#: keeps working, and is never OFFERED, because offering it would re-open
#: ISS-0177's gap — an exception that drops a check with no justification.
#: Four marks, and the vocabulary is settled by measurement rather than taste.
#: Across every acceptance suite in the fleet on 2026-08-17: `x` 851, blank
#: 152, `~` 7, `F` 1, and **`!` zero**. `[!]` was minted in this repo and
#: written nowhere, so it stays READABLE and is never offered — Edwin, asked
#: directly: *"I have no problem using ~ instead."*
#:
#: ===========  ========  ==========================================  ========
#: mark         walked?   means                                       blocks
#: ===========  ========  ==========================================  ========
#: ``[ ]``      no        nobody has done it                          yes
#: ``[x]``      yes       passed                                      no
#: ``[~]``      no        could not be run, and is not holding the    no
#:                        release — Edwin 2026-08-17
#: ``[F]``      yes       walked and failed, tracked                  yes
#: ===========  ========  ==========================================  ========
#:
#: `[ ]` and `[F]` both block and mean **opposite** things about whether the
#: work was done, which is why `F` earns a mark rather than collapsing into
#: blank. `[~]` and `[x]` both pass the gate and mean opposite things about
#: whether anything was verified — which is why `[~]` cannot be written
#: without a reason.
#: **Words, not characters** (ADR-0034 decision 5, ISS-0200). Minimal's
#: distinctions kept; Minimal's notation dropped. The notation was adopted
#: because the suite WAS a Markdown document that Obsidian rendered; the
#: document is gone and a `mark: "/"` in frontmatter is a lookup, not a render.
VERDICTS: dict[str, str] = {
    "pass": "done",
    "partial": "incomplete",
    "excused": "canceled",
    "failed": "important",
    "question": "question",
    "clear": "todo",
    #: **The seventh, and the one that pays for the migration.** An invalidated
    #: check was written as `mark: " "` plus an `invalidated_by:` block --
    #: *"nobody has walked it"* recorded against a check somebody walked. The
    #: two states were the same value in the one field every surface reads, so
    #: telling them apart needed a date comparison. `your-trainer` carries 54.
    "rerun": "rerun",
}
#: The characters, read forever and never written (ADR-0029, ADR-0034). Every
#: repo that has not migrated its vocabulary keeps working, and `suite_at`
#: reads twelve historical tags where only characters exist.
LEGACY_MARKS: dict[str, str] = {
    "~": "incomplete", "F": "important", "X": "done",
    "x": "done", "/": "incomplete", "-": "canceled",
    "!": "important", "?": "question", " ": "todo", "": "todo",
}
def normalise_mark(raw: str) -> str:
    """A mark as a word, whatever it was written as.

    One place translates, and it runs on **read** rather than at each
    comparison — so every surface, every gate and every count sees the same
    vocabulary whether the note was authored today or two migrations ago, and
    `suite_at` can read twelve historical tags that contain only characters.
    """
    mark = str(raw or "")
    # **Never `.strip()` the character form.** `" x"` and `"x "` are exactly the
    # typos `_ITEM_RE` refuses to normalise -- its own comment says *"`\" x\".strip()`
    # is `\"x\"`, so a parser written from that comment would read a typo as a
    # walked check"* -- and stripping here moved them from *unrecognised and
    # therefore blocking* to `done` and settled. Found by independent review; it
    # is the one change in this migration that could let a release through on a
    # check nobody walked.
    #
    # A WORD is stripped and lowercased, because YAML scalars legitimately carry
    # surrounding space and `Done` is not a typo. A character is matched exactly.
    if mark in LEGACY_MARKS:
        return LEGACY_MARKS[mark]
    word = mark.strip().lower()
    if word in _ALL_WORDS:
        return word
    if not mark.strip():
        return "todo"
    # Unrecognised, verbatim -- which every gate reads as blocking.
    return mark


#: Every legal word. Anything else stays verbatim and is therefore unrecognised,
#: which the gate reads as blocking — the direction that fails safely.
_ALL_WORDS: frozenset[str] = frozenset(
    {"done", "incomplete", "canceled", "important", "question", "todo", "rerun"})

#: Refused without a reason. The mark and its justification are one action, so
#: a check cannot leave the gate silently — the whole gap [[ISS-0177]] records
#: for `[!]`, which shipped its permissive half with no way to ask why.
VERDICTS_NEEDING_REASON: frozenset[str] = frozenset({
    "partial", "excused", "failed", "question",
})
#: Ids named in a reason, linkified on write and checked by the caller.
_REASON_ID_RE = re.compile(r"\b([A-Z]{2,6}-\d{3,4})\b")
# `_escape_reason` lived here and went with the row grammar (ISS-0192). It
# flattened a reason to one line, stripped every metacharacter that could
# escape a list item, and linkified any id it found — all of which mattered
# because the reason was appended to a Markdown row. A `verdict_reason:` field
# is a YAML scalar, so `note_writes._yaml_safe` does the flattening and the
# quote-escaping that matter there, and nothing linkifies: the field is text.
#
# `_REASON_ID_RE` stays for `issue_refs_in` below, which is the half that was
# never about rendering — it tells the caller which ids a reason names so the
# write can be REFUSED when one of them resolves to nothing.


def issue_refs_in(reason: str) -> tuple[str, ...]:
    """Project-os ids a reason names, so the caller can check they resolve.

    Returned rather than linkified here: whether an id resolves is a question
    for the index, which this module deliberately does not import.
    """
    return tuple(dict.fromkeys(_REASON_ID_RE.findall(reason or "")))
