"""What the record owes a person, enumerated **by note type** (TASK-0369).

ADR-0020: *an obligation surfaces in the view that owns its subject*, and the
count lives on the view button. That is only enforceable if the kinds exist as
data — so this is the data, and it is the single source. `GET /api/notes/actions`
and the per-view badges both read it; no renderer restates it.

**By type, not by obligation kind, and that inversion is the whole design.**
The first cut of this module listed seven kinds by name, drawn from the review
desk's contents. It was wrong three times in one day — `change` (116 notes, 76
unreviewed), `release`, then `risk`/`workflow`/`phase` (40 between them). Each
was found by Edwin asking "what about X?", never by anything failing, because a
list written from one surface cannot know what was never on it.

Enumerating by type inverts the burden: **the corpus supplies the checklist.**
A type present in the notes with no declaration is a test failure rather than
something somebody has to notice.

**`NONE` is explicit and carries its reason.** `task` (381 notes) and `plan`
(52) genuinely owe nothing — correct, load-bearing, and indistinguishable from
an omission when unwritten. That is what makes the completeness test mean
something instead of being a formality.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from . import statuses as _statuses

if TYPE_CHECKING:  # pragma: no cover
    from .index import Index

#: The views an obligation may be owned by. One type, one view — otherwise the
#: badges count it twice or neither.
VIEW_OVERVIEW = "overview"
VIEW_INTENT = "intent"
VIEW_FEATURES = "features"
VIEW_ISSUES = "issues"
VIEW_TESTS = "tests"
#: The third phase's view (ADR-0028 / FEAT-0102). Publication's obligations
#: used to sit on `overview` — a view named for *everything* — because
#: publication had no home. `overview` is also not a nav mode, so those rows
#: reached no navigator at all and had to be hand-carried to the attention
#: panel (TASK-0418). This is the home, and it is a real mode.
VIEW_PUBLICATION = "publication"

VIEWS: frozenset[str] = frozenset({
    VIEW_OVERVIEW, VIEW_INTENT, VIEW_FEATURES, VIEW_ISSUES, VIEW_TESTS,
    VIEW_PUBLICATION,
})


@dataclass(frozen=True)
class Obligation:
    """One kind of owed judgment, or an explicit absence of one."""

    #: Statuses that make a note of this type owed. Empty means "not driven by
    #: status" — see `predicate` — or, with `owed=False`, nothing at all.
    states: tuple[str, ...] = ()
    view: str = ""
    verb: str = ""
    owed: bool = True
    #: Why this type owes nothing. **Required** when `owed` is False: an
    #: unexplained absence is what an omission looks like from the outside.
    reason: str = ""
    #: Set when the obligation is not a plain status match, so a reader knows
    #: the predicate lives elsewhere rather than assuming this is the whole rule.
    predicate: str = ""
    #: Resolves the view **per item** when the phase that owns a note's subject
    #: is not decided by its type (ADR-0028). ``None`` keeps `view` above,
    #: which is what every single-phase corpus uses.
    #:
    #: **A view is a corpus; a phase is not.** `issues` spans all three phases
    #: and `tests` spans two — only `intent` and `publication` sit wholly in
    #: one. The registry has only ever had the corpus axis, so an obligation's
    #: phase was implicit in its TYPE: right for the corpora that do not span,
    #: silently wrong for the ones that do. That is one gap, and it surfaced
    #: twice — as `tests` straddling, and as publication having nowhere to
    #: live but `overview`.
    #:
    #: So per-item routing is not an exception mechanism. It is the only
    #: correct one; fixed-per-type merely happened to give the right answer
    #: often enough never to fail loudly.
    route: "Callable[[Any], str] | None" = None


def NONE(reason: str, view: str = "") -> Obligation:  # noqa: N802 — reads as a literal
    return Obligation(owed=False, reason=reason, view=view)


def view_for(record: Any, ob: Obligation) -> str:
    """Which view owns this item's obligation (ADR-0028 decision 2).

    The declared `view` unless the type carries a `route`. Callers use this
    instead of reading `ob.view`, so a spanning corpus cannot be routed by one
    walk and mis-routed by another — the property `obligations.py` exists to
    guarantee, restated for the axis this decision adds.
    """
    if ob.route is None:
        return ob.view
    return ob.route(record) or ob.view


#: Every note type in the corpus. A type here with no entry fails a test.
OBLIGATIONS: dict[str, Obligation] = {
    # ---- owed ----------------------------------------------------------
    "adr": Obligation(("proposed",), VIEW_INTENT, "Decide"),
    "decision": Obligation(("proposed",), VIEW_INTENT, "Decide"),
    "design": Obligation(("proposed",), VIEW_INTENT, "Accept"),
    #: **A surface asks for nothing** ([[TASK-0514]]). It is a place in the
    #: product, not work: it exists until the product stops having it, and
    #: `retired`/`superseded` are facts rather than obligations. What a surface
    #: MAKES visible -- that it carries no checks -- is a question about the
    #: SUITE and belongs to the tests view, which already asks it. An
    #: obligation here would count the same gap twice on two badges.
    "surface": NONE(
        "a surface is a place, not work: it exists until the product stops "
        "having it. An uncovered surface is a fact about the SUITE, asked "
        "where the suite is (TASK-0516), not a debt the surface owes.",
        VIEW_TESTS,
    ),
    "requirement": Obligation(("draft", "proposed"), VIEW_FEATURES, "Approve"),
    "issue": Obligation(("triage",), VIEW_ISSUES, "Triage"),
    "test": Obligation(
        ("ready",), VIEW_TESTS, "Run",
        # **One verb for one act** (TASK-0495, then TASK-0521 which reversed
        # it). The registry once carried `Run` here and `Walk` on the release
        # gate — one act, two verbs, live as *"Run 5 tests"* beside *"Walk 1
        # release gate"*. TASK-0495 unified on `Walk`, arguing that a person
        # walks a procedure and a machine runs a `command:`.
        #
        # **DES-0012 D2 removed that premise.** With `command:` the single
        # answer to who runs a test, one verb covers both populations: a test
        # with a command is run by a runner, one without is run by a person.
        # Edwin: *"can you stop talking about 'walking'."*
        #
        # Both changes were argued from the same fact and reached opposite
        # conclusions. The tie-break is that a reader should not need the
        # argument — and `Run` is the word people already use.
        predicate="tests a person runs — one with a `command:` waits on a "
                  "runner, not on anybody",
    ),
    "feature": Obligation(
        (), VIEW_FEATURES, "Accept",
        predicate="`acceptance: requested` in frontmatter, not a status "
                  "(DES-0006's opt-in gate)",
    ),
    # ADR-0023 retired this obligation on 2026-08-11. It was the largest one
    # in the registry — the overview badge read 87 and **all 87 were change
    # reviews** — and the decision it enforced (`ADR-0011`) does not exist in
    # any repo: upstream `docs/decisions/` holds a README and nothing else.
    # A change note records what happened; the review that catches something
    # happens at the gates below, against the diff, while the work is live.
    "change": NONE(
        "ADR-0023: a change note is a record, not a claim. Reviewing the note "
        "months later reviews the prose; the review that matters happens on "
        "the TST-* note, the requirement, the feature and the release.",
        VIEW_OVERVIEW,
    ),

    # ---- owed nothing, and why -----------------------------------------
    "task": NONE(
        "agent-owned end to end: backlog -> doing -> done carries no human "
        "judgment. STATUSES.md's ownership table assigns every task transition "
        "to the agent.",
        VIEW_FEATURES,
    ),
    "plan": NONE(
        "a plan's status follows its parent feature and is advanced at "
        "close-out (STATUSES.md). `draft` on a plan means the feature has not "
        "started, not that anyone owes it a decision — which is why plans were "
        "removed from the review desk queue on 2026-07-26.",
        VIEW_FEATURES,
    ),
    "phase": NONE(
        "closing a phase is a PROCEDURE that follows the work, not a judgment "
        "somebody is holding up: re-home the children, tick the exit criteria "
        "with evidence, set `superseded_by`, update PHASES.md and the snapshot. "
        "There is no single transition an actuator could offer, and "
        "`phase_close_blockers()` already reports when closing is POSSIBLE — a "
        "gate, not a debt. The Overview's `unclosed` pill stays as a mark. "
        "(Edwin, 2026-08-10 — ISS-0128.)",
        VIEW_FEATURES,
    ),
    "risk": NONE(
        "`open` is a risk's resting state. A risk is a hazard the project has "
        "decided to CARRY, and carrying one is not a debt — it may never "
        "arrive. All six here have sat at `open` since they were written, and "
        "that is correct rather than neglected. (Edwin, 2026-08-10 — ISS-0128.)",
        VIEW_INTENT,
    ),
    "workflow": NONE(
        "workflows document the TOOLING, not this project's lifecycle. "
        "WF-0001..0003 ship with the template under `group:maintainers` and "
        "describe `project-derive`, `sync-project-os.sh` and `snapshot-sync`. "
        "This repo received them; it does not curate them, so their `draft` is "
        "not a claim about anything it owes. (Edwin, 2026-08-10 — ISS-0128.)",
        VIEW_INTENT,
    ),
    "release": NONE(
        "the release GATE is a test obligation, not a release one — its "
        "subject is an unchecked Tier 1/2 test, so it surfaces in Tests "
        "(ADR-0020 amendment 11). The Overview owns the release RECORD.",
        VIEW_OVERVIEW,
    ),
    "reference": NONE(
        "a standing document has no lifecycle. Its state is freshness, which "
        "FEAT-0091's manifest reports as missing / ambiguous / stub / stale — "
        "a warning, never a build error.",
        VIEW_INTENT,
    ),
    "architecture": NONE(
        "a standing document: one per project, no lifecycle, written to be "
        "read. Its state is freshness — ISS-0125 measured this class at 94% "
        "stale fleet-wide — and freshness warns rather than owing.",
        VIEW_INTENT,
    ),
    "glossary": NONE(
        "a standing document: one per project, no lifecycle. A definition is "
        "true or out of date, never owed to somebody; FEAT-0091's manifest "
        "reports the second as a warning.",
        VIEW_INTENT,
    ),
    "dashboard": NONE(
        "removed from this corpus (TASK-0383) — an Obsidian artifact whose "
        "`.base` embeds were all dead. Declared so the type does not reappear "
        "undeclared if a repo still carries one.",
    ),
    # ADR-0030's second exemption, and the one that ADR names as its own
    # biggest risk. Granularity makes 669 acceptance rows individually
    # ADDRESSABLE; it must not make them individually OWED. ADR-0027 called
    # this population *"the most self-re-arming population in the corpus"* — a
    # check clears, a change lands, it is owed again, forever, on a badge — and
    # nothing about that reasoning changed when the rows became notes. It
    # acquired 669 new subjects.
    #
    # The release gate stays ONE campaign row whose subject is *the suite has
    # unwalked Tier 1/2 checks*, never a particular check. `your-trainer`'s
    # badge total is measured across each migration leg for exactly this
    # reason: this is the one place in the phase where it could move.
    #
    # Declared rather than omitted, and the declaration is the mechanism: the
    # completeness test asserts every type in the corpus has an entry here, so
    # a `check` note appearing with no declaration is a test failure rather
    # than a silent default. The exemption is a sentence somebody had to write.
    "check": NONE(
        "ADR-0030: an acceptance check is run by a person, not owed. ADR-0027 measured "
        "acceptance rows as the most self-re-arming population in the corpus — "
        "each re-arms on every change that touches it — so per-check "
        "obligations are the one use of this granularity that is forbidden "
        "outright. The release gate stays a single campaign row in Tests.",
        VIEW_TESTS,
    ),
}


#: The standing set's obligation — the one entry whose subject is **not a note
#: type** (TASK-0382).
#:
#: `architecture`, `glossary` and `reference` each declare `NONE` above, and
#: correctly: most `reference` notes are not standing documents at all (11 in
#: this repo's Reference group, 5 of them singletons), so making the TYPE owed
#: would count the wrong population. The subject here is a **manifest entry**,
#: which the type-keyed table has no way to express — so it is declared
#: separately rather than forced into a shape it does not fit.
#:
#: **Missing, ambiguous and stub count; stale does not.** The first three are
#: binary and one act clears each: write the document, delete the rival, fill
#: in the template. Staleness returns by the calendar — counting it is a badge
#: that re-arms itself forever, which is the permanent nag this project has
#: been bitten by twice (PHASE-015's close-out pill, `Doing · 44`). It still
#: MARKS the row; it just does not ask.
STANDING_OBLIGATION = Obligation(
    (), VIEW_INTENT, "Confirm",
    predicate="a manifest entry that is missing, ambiguous or holding its "
              "template. Staleness marks the row and does not count.",
)

#: The verb per finding kind (ISS-0153). One constant was wrong for every kind
#: it was applied to: **you cannot confirm a document nobody has written**, and
#: the three owed kinds want three different things. `Confirm` is right for
#: exactly the kind that is deliberately NOT owed — `stale`, meaning *is this
#: still true?* — which is how it came to be the label on all of them.
#:
#: None of these is a status transition, and that is not a gap. The row opens
#: the document, and a surface that says `Write` and then opens the file has
#: told the truth twice; a button would be a third thing to build for an act
#: that is just editing.
STANDING_VERBS: dict[str, str] = {
    "missing": "Create",
    "stub": "Write",
    "ambiguous": "Resolve",
    "stale": "Confirm",
}

#: What the standing obligation calls itself in a per-kind breakdown
#: (ISS-0133). It is the one obligation whose subject is not a note, so it has
#: no `note_type` to be keyed by and needs a name of its own.
STANDING_OBLIGATION_KIND = "standing document"

#: Publication, ADR-0027's first new subject (FEAT-0100). Two kinds rather than
#: one: a repo has exactly one remote kind so only one is ever non-zero, but
#: merging them would put two things a person must treat differently behind one
#: number — `Push` is offered, `Deploy` is named and refused.
PUSH_OBLIGATION_KIND = "unpushed commit"
DEPLOY_OBLIGATION_KIND = "undeployed commit"

#: Every obligation whose subject is not a note. A source here with no rows
#: function, or a kind with no noun, fails a test — the same completeness
#: burden the note-typed side carries, for the same reason.
#:
#: Populated below `_standing_rows`, which it names.
NOTE_LESS: dict[str, "NoteLessObligation"] = {}

#: How a kind names itself when a badge counts it (ISS-0133), singular and
#: plural. Here rather than in the renderer because the obligation vocabulary
#: ships from the server and never from TypeScript (TASK-0357) — a plural rule
#: in the client is a second vocabulary, and `adr` -> `adrs` is exactly the
#: kind of thing it would get wrong on its own.
KIND_NOUNS: dict[str, tuple[str, str]] = {
    "adr": ("ADR", "ADRs"),
    "surface": ("surface", "surfaces"),
    "decision": ("decision", "decisions"),
    "design": ("design", "designs"),
    "requirement": ("requirement", "requirements"),
    "issue": ("issue", "issues"),
    "test": ("test", "tests"),
    "feature": ("feature", "features"),
    "change": ("change note", "change notes"),
    STANDING_OBLIGATION_KIND: ("standing document", "standing documents"),
    # The badge composes `<count> <noun> to <verb>`, so these read as
    # "6 commits to push" and "2 commits to deploy" — the sentence DES-0011
    # asks for, from the registry rather than from a string in the renderer.
    PUSH_OBLIGATION_KIND: ("commit", "commits"),
    DEPLOY_OBLIGATION_KIND: ("commit", "commits"),
    # Singular by construction — a repo prepares one release at a time — but
    # the plural is declared rather than omitted, because a kind with no noun
    # fails the completeness test and silence here would be an omission
    # wearing the shape of a decision.
    "release gate": ("release gate", "release gates"),
}

#: Finding kinds from `standing.check` that the badge counts.
STANDING_OWED_KINDS: frozenset[str] = frozenset({"missing", "ambiguous", "stub"})


# ----- obligations whose subject is not a note (ADR-0027 / TASK-0416) -------
#
# The registry enumerates **by note type**, which is its best idea and stays:
# the corpus supplies the checklist, so a type nobody declared fails a test
# rather than waiting to be noticed.
#
# But not every obligation has a note behind it. The standing document was the
# first — its subject is a manifest entry — and it was carried by two bolt-ons:
# an addition inside `counts_by_kind`, and a second inside the `Needs you`
# group because `owed_items` produced no rows for it. That seam has already
# failed once: *"Intent's group came out 3 against a badge of 5."*
#
# ADR-0027 widened the registry's scope to **what needs a person**, which makes
# note-less obligations the normal case rather than the exception. So they get
# a declared path: one walk yielding a count AND its rows, exactly as the
# note-typed side already does, and asserted the same way.


@dataclass(frozen=True)
class NoteLessObligation:
    """An obligation whose subject is not a note (ADR-0027).

    `rows` returns owed rows in the same shape as :func:`owed_items` produces,
    so a caller never has to know which side of the registry an obligation came
    from. The count is `len(rows)` — never counted separately, because two
    passes over one predicate is how a page and its own button come to
    disagree.
    """

    kind: str      # its key in KIND_NOUNS
    view: str
    verb: str      # the default; a row may carry a more specific one
    rows: "Callable[[Any], list[dict[str, Any]]]"
    predicate: str = ""


def _standing_rows(index: Any) -> list[dict[str, Any]]:
    """Owed manifest entries, as rows (TASK-0416).

    The judgment of *which* kinds are owed, and *what verb* each is owed,
    stays here — `standing.entries` resolves and describes, this decides.
    """
    from . import standing

    try:
        entries = standing.entries(index.docs_root)
    except OSError:                      # pragma: no cover — unreadable tree
        return []
    out: list[dict[str, Any]] = []
    for entry in entries:
        if entry.kind not in STANDING_OWED_KINDS:
            continue
        out.append({
            "id": entry.name,
            "title": entry.question,
            # A standing document may live beside the docs tree rather than
            # inside it, so the row carries its own route rather than letting
            # a caller compose `/docs/<rel>` and land on a dead click.
            "url": entry.url,
            "rel": "",
            "type": STANDING_OBLIGATION_KIND,
            "status": entry.kind,
            "detail": entry.detail,
            "verb": STANDING_VERBS.get(entry.kind, STANDING_OBLIGATION.verb),
        })
    return out


# ----- publication (FEAT-0100 / TASK-0417) ----------------------------------
#
# ADR-0027's first new subject. Committed work that nobody has published is not
# a judgment about the record — it is work already judged and not yet sent —
# which is precisely the widening that decision made: the registry counts what
# needs a **person**, and ADR-0022 made the human the publisher of last resort.
#
# Two kinds, not one. A repo has exactly one remote kind, so only one of these
# is ever non-zero for a given project, but merging them would put two things a
# person must treat differently behind one number: `Push` is offered, `Deploy`
# is named and refused — one fleet repo's only remote is a server path, and
# pushing it publishes a live website.

def _publication_rows(index: Any, kind: str, verb: str,
                      remote_kind: str) -> list[dict[str, Any]]:
    """One row per unpublished commit — the obligation's subjects.

    The count is `len()` of this list, which is why it is not capped: a total
    that outruns its own rows is the disagreement TASK-0416 removed.
    """
    from . import git_state

    project_root = Path(str(index.docs_root)).parent
    try:
        state = git_state.read(project_root)
    except OSError:                      # pragma: no cover — unreadable repo
        return []
    if state.kind != remote_kind:
        return []

    # An UNKNOWN count is not a zero, and rendering it as one is the failure
    # ADR-0027's fourth admission test exists to refuse -- the same test
    # TASK-0415's opening paragraph names as this obligation's gate, and which
    # the shipped code did not honour. `ahead` is None when the count could not
    # be taken at all: a branch with no upstream is the ordinary case, and
    # `git rev-list @{u}..HEAD` simply fails. Independent review demonstrated
    # it on 2026-08-14 -- a real repo, a real github remote, no upstream, and
    # all three surfaces silently reported nothing owed.
    #
    # It is emitted as ONE row rather than a count of commits, because the
    # number of commits is precisely what is not known. What is known is that
    # a person has to do something -- set the upstream -- before publication
    # can be reported at all, which is exactly what this registry counts.
    if state.ahead is None:
        return [{
            "id": "publication-state-unknown",
            "title": "No upstream is set, so nothing can say what is unpublished",
            "url": "~history",
            "rel": "",
            "type": kind,
            "status": state.kind,
            "detail": "unknown",
            "verb": verb,
        }]
    if not state.commits:
        return []
    return [{
        "id": commit.sha,
        "title": commit.subject,
        # History is where the commits live and where the action goes
        # (ADR-0020, DES-0011). The row is a shortcut to its own subject.
        "url": "~history",
        "rel": "",
        "type": kind,
        "status": state.kind,
        "detail": commit.when,
        "verb": verb,
    } for commit in state.commits]


NOTE_LESS[PUSH_OBLIGATION_KIND] = NoteLessObligation(
    kind=PUSH_OBLIGATION_KIND,
    # **Back on `overview`** (ISS-0179). ADR-0028 moved these to `publication`
    # when that view was a LADDER — commit, push, deploy, release — and the
    # rung was their subject's home. FEAT-0107 made the view a list of
    # releases, and a commit is not a release: the rungs went back to
    # `~history` and the overview, where the Push control has always actually
    # lived.
    #
    # The badge had to follow. Edwin: *"you have removed the commits and
    # pushes from this page … if you remove it then it should no longer be
    # included in the badge in the view icon."* A count on a button that opens
    # a view not containing what it counts is worse than no count — it sends
    # the reader somewhere the work is not.
    view=VIEW_OVERVIEW,
    verb="Push",
    rows=lambda index: _publication_rows(
        index, PUSH_OBLIGATION_KIND, "Push", "backup"),
    predicate="a commit on HEAD that the tracked remote does not have, where "
              "that remote is a backup rather than a deployment target",
)

NOTE_LESS[DEPLOY_OBLIGATION_KIND] = NoteLessObligation(
    kind=DEPLOY_OBLIGATION_KIND,
    view=VIEW_OVERVIEW,
    verb="Deploy",
    rows=lambda index: _publication_rows(
        index, DEPLOY_OBLIGATION_KIND, "Deploy", "deploy"),
    # Counted, and NOT offered (Edwin 2026-08-13). ADR-0027 admission test 3
    # requires an action the cockpit can offer **or name**; this is the case
    # that clause was written for. A badge that omitted these would make
    # "nothing owed" false about a repo with a real backlog.
    predicate="the same commits, where the remote is a deployment target — "
              "named here, never pushed from here",
)

NOTE_LESS[STANDING_OBLIGATION_KIND] = NoteLessObligation(
    kind=STANDING_OBLIGATION_KIND,
    view=STANDING_OBLIGATION.view,
    verb=STANDING_OBLIGATION.verb,
    rows=_standing_rows,
    predicate=STANDING_OBLIGATION.predicate,
)


# ----- the release gate (FEAT-0102 / TASK-0429) -----------------------------
#
# **One obligation, never sixty.** The first proposal admitted every unchecked
# Tier 1/2 row to this registry, and Edwin refused it: *"I am also afraid that
# this could overwhelm my attention."* The registry's own charter agrees —
# ADR-0027 excludes staleness because *"counting it is a badge that re-arms
# itself forever"*, and acceptance rows re-arm IN BULK, by the suite's own rule
# 3 (*"code changes must uncheck all tests whose scope overlaps"*). They are the
# most self-re-arming population in the corpus.
#
# So the CAMPAIGN is the obligation. 60 is a number it states; no badge ever
# sums it. `your-trainer`'s 60 blocking rows cluster into 17 sections and two
# of those carry 33 — roughly two sittings, most of it with a trainer plugged
# in. That is not sixty things to do.
#
# And it asks only while a release is `draft`. With none in preparation, an
# unchecked suite is the resting state of a checklist that unchecks itself
# whenever code changes (ADR-0028 decision 3) — not a debt.

GATE_OBLIGATION_KIND = "release gate"


def _gate_rows(index: Any) -> list[dict[str, Any]]:
    """One row while a release is being prepared and the gate is blocked."""
    from . import acceptance, publication

    try:
        draft = publication.preparing(index)
    except OSError:                      # pragma: no cover — unreadable tree
        return []
    if draft is None:
        return []
    gate = acceptance.gate_payload(index.docs_root)
    if not gate.get("exists") or not gate.get("blocked"):
        return []
    unchecked = sum(
        int(c.get("unchecked") or 0) for c in (gate.get("counts") or {}).values()
    )
    return [{
        "id": str(draft["id"]),
        "title": f"{unchecked} Tier 1/2 checks stand between "
                 f"{draft.get('version') or draft['id']} and shipping",
        "url": "~publication",
        "rel": str(draft.get("rel") or ""),
        "type": GATE_OBLIGATION_KIND,
        "status": "draft",
        "detail": f"{unchecked} unchecked",
        "verb": "Run",
        # The route the verb PERFORMS, so the action rides the row rather
        # than a group header (Edwin: *"that walk button looks totally out of
        # place there"*). Every other owed row names a verb and has nowhere to
        # put it; this is the first to carry one.
        "action": "~walk",
    }]


NOTE_LESS[GATE_OBLIGATION_KIND] = NoteLessObligation(
    kind=GATE_OBLIGATION_KIND,
    view=VIEW_PUBLICATION,
    verb="Run",
    rows=_gate_rows,
    predicate="a release at `draft` whose acceptance tests still have unchecked "
              "Tier 1/2 items — ONE row for the campaign, never one per check",
)


# ----- the acceptance sweep: WITHDRAWN (ADR-0036) ---------------------------
#
# Removed 2026-08-18 on Edwin's instruction, with the reasoning in [[ADR-0036]].
# It asked an in-flight feature *what did this change do to the acceptance
# suite?* and was built (FEAT-0115) from a measured problem: 54 rows across the
# fleet carried a hand-written `RE-RUN (…)` and all 54 were still ticked.
#
# **That population is now empty.** `mark: rerun` and `invalidated_by:` are 0 in
# every repo. What was left was the asking — and on the day of the decision five
# of the six features owing a sweep had been created that afternoon, none of
# them touching an acceptance check.
#
# `acceptance_impact:` values already written are LEFT IN THE NOTES. They record
# that somebody considered the question on a date, which stays true whether or
# not anything reads it.
#
# When invalidation matters again, key the replacement on the SURFACE a change
# touched rather than on the feature (DES-0012).



#: Where the per-index memo lives. **On the index itself**, not in a module
#: dict keyed by `id(index)` — which is what this was, and which is unsound:
#: CPython reuses an address once the object at it is collected, so a freed
#: index and a fresh one allocated in its place would share a key. Both are
#: routinely at `generation` 0 (a newly built index always is), so the second
#: half of the key would not save it, and the wrong corpus's owed rows would be
#: served for a corpus that owes nothing.
#:
#: Hung off the object instead, so the memo cannot outlive what it describes.
#: Identity reuse becomes unrepresentable rather than unlikely.
_MEMO_ATTR = "_note_less_owed_memo"


def note_less_row_for(index: "Index", note_id: str) -> dict[str, Any] | None:
    """A note-less obligation's row naming this note, if one does.

    **Note-less does not mean note-free.** A note-less obligation may still have
    a note as its subject — it lives on that side of the registry when it is
    keyed on something the per-type table cannot express, such as a MISSING
    field (one type carries one entry). So an item can appear in Needs-you
    through this source while its row in the tree is marked through the other,
    and the tree has to consult both or the same item shows up twice with only
    one of the two saying why.

    The acceptance sweep was the worked example until [[ADR-0036]] withdrew it;
    the shape it needed is still here because the next such obligation will
    need it too.
    """
    if not note_id:
        return None
    generation = int(getattr(index, "generation", 0))
    memo = getattr(index, _MEMO_ATTR, None)
    if memo is None or memo[0] != generation:
        rows_by_id: dict[str, dict[str, Any]] = {}
        for rows in note_less_rows(index).values():
            for row in rows:
                if row.get("id") and row.get("rel"):
                    rows_by_id.setdefault(str(row["id"]), row)
        memo = (generation, rows_by_id)
        try:
            setattr(index, _MEMO_ATTR, memo)
        except AttributeError:          # pragma: no cover — a slotted stub
            pass
    return memo[1].get(note_id)


def note_less_sources() -> dict[str, "NoteLessObligation"]:
    """Every declared note-less obligation, keyed by kind."""
    return dict(NOTE_LESS)


def note_less_rows(index: Any) -> dict[str, list[dict[str, Any]]]:
    """Owed rows per view from every note-less source — the one walk."""
    out: dict[str, list[dict[str, Any]]] = {v: [] for v in VIEWS}
    for source in NOTE_LESS.values():
        out[source.view].extend(source.rows(index))
    return out


def standing_owed(docs_root: Any) -> int:
    """How many manifest entries are owed a person's attention.

    Kept as the narrow question some callers still ask, but derived from the
    rows rather than counted independently — the count and the list cannot
    disagree if only one of them is computed.
    """
    class _Shim:
        pass

    shim = _Shim()
    shim.docs_root = docs_root  # type: ignore[attr-defined]
    return len(_standing_rows(shim))


def declared_types() -> frozenset[str]:
    return frozenset(OBLIGATIONS)


def for_type(note_type: str | None) -> Obligation | None:
    return OBLIGATIONS.get((note_type or "").strip().lower())


def owed_kinds() -> dict[str, Obligation]:
    """Only the types that owe something — what the badges count."""
    return {k: v for k, v in OBLIGATIONS.items() if v.owed}


def views_owed() -> dict[str, list[str]]:
    """Which types each view is answerable for."""
    out: dict[str, list[str]] = {v: [] for v in sorted(VIEWS)}
    for note_type, ob in OBLIGATIONS.items():
        if ob.owed and ob.view:
            out[ob.view].append(note_type)
    return out


def payload() -> dict[str, Any]:
    """The registry as data, for renderers that draw what they are sent."""
    return {
        "views": sorted(VIEWS),
        "kinds": [
            {
                "type": note_type,
                "states": list(ob.states),
                "view": ob.view,
                "verb": ob.verb,
                "predicate": ob.predicate,
            }
            for note_type, ob in sorted(OBLIGATIONS.items()) if ob.owed
        ],
        "none": [
            {"type": note_type, "reason": ob.reason, "view": ob.view}
            for note_type, ob in sorted(OBLIGATIONS.items()) if not ob.owed
        ],
    }


# ----- the in-flight rule (ADR-0028 decision 3 / TASK-0424) -----------------
#
# An obligation asks while a subject it names is being worked, and rests
# otherwise. This is the rule the registry ALREADY applies to risks — *"`open`
# is a risk's resting state … carrying one is not a debt"* — and to staleness,
# applied to the two populations that have the problem.
#
# Measured in `your-trainer` on 2026-08-16, which is where Edwin reported it:
# 23 of 26 owed requirements attach to features still in `backlog` and 21 of
# the 26 belong to a phase literally named `PHASE-999-Future`; 10 of 15 owed
# manual tests verify only `done` or system-wide work and had sat at `ready`
# for four to seven months. 64 owed items become 31.

#: A subject that is **not** being worked: terminal, or not started.
#:
#: **Derived from `statuses`, never hand-listed**, and the first draft was
#: hand-listed and wrong within the hour. It named the terminal statuses of
#: *features* — `done`, `cancelled`, `superseded` — and a test's subject can
#: equally be a requirement or an issue, whose terminal values are
#: `implemented`, `retired` and `fixed`. Those fell through to the
#: unrecognised-status branch and asked forever: measured on `your-trainer`,
#: 8 owed tests where the rule should have left 5, and all three of the extras
#: were that one gap. Deriving means a status added upstream is resting on
#: arrival rather than becoming a permanent question.
#:
#: `backlog` and `deferred` are added because neither is *terminal* — the first
#: is work not started, the second is work parked — and both are exactly the
#: resting state this rule exists to stop counting. `planned` is deliberately
#: NOT here: `backlog` -> `planned` -> `doing` is the sequence STATUSES.md
#: documents, so `planned` means scheduled, and approving the requirements of
#: the thing you are about to build is live work.
RESTING_STATES: frozenset[str] = (
    _statuses.COMPLETED_STATUSES | frozenset({"backlog", "deferred"})
)
#: Types the rule applies to, with the frontmatter naming their subject.
#: **Exactly two** (ADR-0028's table). `issue` is deliberately absent: triage
#: is owed because nobody has READ it yet, so its subject is the issue itself
#: and it is owed in every phase.
SUBJECT_FIELDS: dict[str, tuple[str, ...]] = {
    "requirement": ("implements",),
    # `covers` FIRST, and the three after it are the legacy names it renamed
    # (ADR-0032). Missing it was a silent disarming rather than an error:
    # ADR-0032 deleted `verifies`/`features`/`requirements` from every test in
    # this repo, so `subject_ids` resolved nothing for 77 of 77 notes, and
    # `subject_is_in_flight` treats a subject-less note as LIVE by design --
    # which switched ADR-0028's in-flight quieting off for the entire test
    # population and moved the badge from 1 to 3 with nothing reporting it.
    # Found by independent review, not by a guard; the guard now exists.
    "test": ("covers", "verifies", "features", "requirements"),
}

_SUBJECT_ID_RE = re.compile(r"([A-Z]{2,6}-\d{3,4})")


def subject_ids(record: Any) -> tuple[str, ...]:
    """The ids this obligation's subject-bearing fields name."""
    fields = SUBJECT_FIELDS.get(record.note_type or "", ())
    out: list[str] = []
    for field_name in fields:
        raw = record.frontmatter.get(field_name)
        if raw is None:
            continue
        values = raw if isinstance(raw, (list, tuple)) else [raw]
        for value in values:
            for found in _SUBJECT_ID_RE.findall(str(value)):
                if found not in out:
                    out.append(found)
    return tuple(out)


def subject_is_in_flight(record: Any, index: "Index") -> bool:
    """Whether any subject this note names is being worked.

    **A note naming no subject asks.** `your-trainer`'s TST-0001 and TST-0002
    are `scope: system` with no features — under a naive reading they become
    never-owed, which LOSES two tests rather than quieting them. Nothing can
    prove a subject-less obligation is resting, so it is treated as live. That
    is the direction that fails safely, and it is the clause most likely to be
    got wrong.

    **An unrecognised status also asks.** A status in neither set is not
    evidence of rest, and silently quieting on one would make every future
    status value a way to disappear from the badge.
    """
    return ids_in_flight(subject_ids(record), index)


#: **Not built yet** — the only reason an acceptance row goes quiet.
#:
#: This is deliberately NOT :data:`RESTING_STATES`, and the difference is the
#: whole of TASK-0447. Applying the requirement/test rule verbatim to
#: acceptance rows quieted **60 of `your-trainer`'s 60** and the gate vanished,
#: because `RESTING_STATES` contains `done` and `fixed` and almost every
#: acceptance row names a shipped feature or a fixed issue.
#:
#: That is the correct answer for a *requirement* — approving one attached to a
#: finished feature is busywork — and exactly the wrong answer for an
#: *acceptance row*, which verifies user-visible behaviour and is therefore
#: **most** worth walking once the behaviour ships. A regression suite whose
#: rows go quiet the moment their feature is done is a regression suite that
#: only ever tests unfinished work.
#:
#: So the rule for this population is the narrow one it was always described
#: as: *"a screen that does not exist cannot be walked."* Everything else asks,
#: including every issue-workflow state (`open`, `triage`, `ready`) — those are
#: states where the safe direction is to ask, not to hide.
NOT_YET_BUILT: frozenset[str] = frozenset({
    "backlog", "planned", "proposed", "draft", "deferred",
})


def ids_are_unbuilt(ids: "tuple[str, ...] | list[str]", index: "Index") -> bool:
    """Whether **every** subject named is a thing that does not exist yet.

    ``False`` for no ids, an unresolvable id, or any subject in any other
    state — absence of evidence is not evidence of rest, and this is the
    direction that fails safe. ``any`` built subject makes the row walkable,
    which mirrors :func:`ids_in_flight`'s any-in-flight clause.
    """
    if not ids:
        return False
    for note_id in ids:
        path = index.by_id(note_id)
        subject = index.get(path) if path is not None else None
        if subject is None:
            return False
        if (subject.status or "").strip().lower() not in NOT_YET_BUILT:
            return False
    return True


import re as _re_ids

#: A bare id inside a ref that may be a wikilink: `[[ISS-0162-Slug]]` -> `ISS-0162`.
_ID_IN_REF = _re_ids.compile(r"[A-Z]+-\d+")


def ids_are_settled(ids: "tuple[str, ...] | list[str]", index: "Index") -> bool:
    """Whether **every** subject named is finished ([[TASK-0526]]).

    The mirror of :func:`ids_are_unbuilt`, at the other end of the life. That
    one rests a check whose subject does not exist yet; this rests one whose
    subject is done — a Tier 2 regression guard whose issue is closed.

    **Why resting and not retiring.** `TESTING.md` says Tier 2 is *"kept
    permanently"*; Edwin says *"there should be very few tier-2 items active at
    any given time"*. Both are right and they are about different things: the
    check is **kept**, and it is not **asked about**. A rule that retired it
    could not express the case that makes resting correct — the issue reopens,
    and the guard wakes on its own with no bookkeeping anywhere.

    **`is_done_status`, not the band test** ([[ISS-0245]]). `band_of("accepted")`
    is `active`, so a band test would never rest a check guarding an `adr` or a
    `requirement`. That defect was live in `_verdict_is_owed` until today; this
    is written after it rather than before.

    `False` for no ids and for any unresolvable one — absence of evidence is not
    evidence of rest, the same direction `ids_are_unbuilt` fails in.
    """
    if not ids:
        return False
    from .cockpit import is_done_status

    for note_id in ids:
        match = _ID_IN_REF.search(str(note_id))
        resolved = match.group(0) if match else str(note_id)
        path = index.by_id(resolved)
        subject = index.get(path) if path is not None else None
        if subject is None:
            return False
        if not is_done_status(subject.note_type, subject.status):
            return False
    return True


def ids_in_flight(ids: "tuple[str, ...] | list[str]", index: "Index") -> bool:
    """The in-flight rule over bare ids — ADR-0028 decision 3, one copy.

    Split out of :func:`subject_is_in_flight` so an **acceptance row** can use
    it (FEAT-0108 / TASK-0447). A row's subject is not a note, it is the ids
    its section heading names, so there is no `record` to pass — and writing a
    second copy of the predicate for that caller is how the two would come to
    disagree about `deferred` or about a status nobody declared.

    **In flight if ANY subject is.** A section naming several features —
    `## 1.2 Hardware Connectivity (FEAT-0001, FEAT-0007)` — is walkable while
    one of them is live; requiring all of them to be live would quiet a row
    somebody could act on today.
    """
    if not ids:
        return True
    for note_id in ids:
        path = index.by_id(note_id)
        subject = index.get(path) if path is not None else None
        if subject is None:
            # A subject the corpus does not carry cannot be shown to be
            # resting either — same reasoning as the subject-less case.
            return True
        status = (subject.status or "").strip().lower()
        if status in RESTING_STATES:
            continue
        # **A requirement does not vote independently of the feature it
        # implements** (ISS-0202). The ANY rule above was written for PEERS —
        # *"a section naming several features is walkable while one of them is
        # live"* — and a feature together with its own requirements are not
        # peers: a `draft` requirement of a `backlog` feature is the same fact
        # counted twice, in the direction that asks.
        #
        # Measured across all twelve repos: this quiets exactly ONE note,
        # `project-os-cockpit`'s TST-0024, whose FEAT-0099 is `backlog` in a
        # `planned` phase while REQ-0035/0036 sit at `draft`. Asking somebody to
        # hand-walk a remote-SSH procedure for a feature nobody has started is
        # the noise ADR-0028 exists to remove.
        #
        # Deliberately NOT the broader "all subjects must be live" rule, which
        # the same sweep showed silencing four tests whose subjects include a
        # feature at `doing` — including `your-trainer`'s iOS parity walk.
        if subject.note_type == "requirement":
            owner = str(subject.frontmatter.get("implements") or "").strip()
            owner_id = re.search(r"([A-Z]{2,6}-\d{3,4})", owner)
            if owner_id:
                owner_path = index.by_id(owner_id.group(1))
                owner_rec = index.get(owner_path) if owner_path else None
                if owner_rec is not None and (
                        owner_rec.status or "").strip().lower() in RESTING_STATES:
                    continue
        return True          # in flight, or a status nobody declared
    return False


def resting_reason(
    ids: "tuple[str, ...] | list[str]", index: "Index",
) -> list[dict[str, str]]:
    """Why a quiet row is quiet — every subject and its status.

    ADR-0028 decision 5: derived silence must be inspectable. A collapsed group
    that cannot say *which* subject is at rest is indistinguishable from a
    surface that lost the row.
    """
    out: list[dict[str, str]] = []
    for note_id in ids:
        path = index.by_id(note_id)
        subject = index.get(path) if path is not None else None
        out.append({
            "id": note_id,
            "status": (subject.status or "") if subject else "",
            "title": (subject.title or "") if subject else "",
            "rel": (subject.rel_path or "") if subject else "",
        })
    return out


# ----- counting what is actually owed ---------------------------------------


def _is_owed(record: Any, ob: Obligation, index: "Index | None" = None) -> bool:
    """Whether this note is currently owed under its type's declaration."""
    if not ob.owed:
        return False
    status = (record.status or "").strip().lower()

    if record.note_type == "feature":
        return str(record.frontmatter.get("acceptance") or "").strip().lower() == "requested"

    if record.note_type == "test":
        # Manual only: an automated test at `ready` waits on a runner, not a
        # person.
        if status not in ob.states:
            return False
        # **One predicate, and it is the reader's** (ADR-0034 / REQ-0041). This
        # asked whether `kind`/`level`/`runner` contained the word "manual" and
        # never read `command:` at all -- so the rule filling this badge was the
        # weaker of the two, and 8 of 788 fleet tests disagreed with
        # `_is_manual_test`. None involved a `command:`, which is why nothing
        # broke and why nothing would have announced it when it did.
        #
        # Imported inside the function: `cockpit` imports this module, and a
        # module-level import would be a cycle. The same shape `acceptance` and
        # `publication` are already brought in with, one function down.
        from .cockpit import _is_manual_test

        if not _is_manual_test(record):
            return False
    elif status not in ob.states:
        return False

    # The in-flight rule, last: a note must first be owed at all under its own
    # declaration, and only then is it asked whether its subject is live.
    # `deferred` never reaches here — it is not in any owed `states` — which is
    # what makes it the OVERRIDE rather than a second copy of this rule
    # (ADR-0028 decision 6): a deferred requirement stays quiet even when its
    # feature moves to `doing`.
    if index is not None and record.note_type in SUBJECT_FIELDS:
        return subject_is_in_flight(record, index)
    return True


def counts_by_kind(index: "Index") -> dict[str, dict[str, int]]:
    """Owed items per view, **split by the kind that owes them** (ISS-0133).

    The badge has always shown a bare number, and the only explanation of it
    was a tooltip reading `N items here need a person` — the same sentence
    under every view, naming nothing. The kinds have been data since this
    module replaced a hand-written list of seven, so the breakdown costs one
    dict instead of one int and the surface stops having to say "items".

    **Derived from `owed_items`, not walked separately** (TASK-0423). It used
    to be its own pass, asserted equal by a test — a property that has to be
    *maintained*. Note-less obligations were already counted this way for the
    same reason; now every kind is, and the disagreement is unrepresentable
    rather than merely absent.
    """
    out: dict[str, dict[str, int]] = {v: {} for v in VIEWS}
    for view, rows in owed_items(index).items():
        for row in rows:
            kind = str(row["type"])
            out[view][kind] = out[view].get(kind, 0) + 1
    return out


def owed_items(index: "Index") -> dict[str, list[dict[str, Any]]]:
    """The **rows** behind :func:`counts_by_kind`, per view (TASK-0387).

    The badge said a number and the view never gathered what it counted, so a
    reader who saw `4` had to go looking (Edwin, 2026-08-11: *"it is very
    unclear what they relate to … these items need to be immediately visible
    so the user can resolve them"*).

    **The same walk as `counts_by_kind`, deliberately.** Two passes over one
    predicate is how a page and its own button come to disagree, which is the
    failure this module exists to prevent — so this is the walk, and
    `counts_by_kind` is asserted against it rather than the other way round.

    **Note-less obligations are included** (TASK-0416). They used not to be —
    the standing document's subject is a manifest entry, so this walk skipped
    it while `counts_by_kind` added it, and the two surfaces disagreed by
    exactly that number. A caller may now infer the count from `len()`, which
    is the property that makes the disagreement unrepresentable rather than
    merely absent.
    """
    return _walk(index)[0]


def suppressed_items(index: "Index") -> dict[str, list[dict[str, Any]]]:
    """Rows the in-flight rule quieted, per view (ADR-0028 decision 5).

    **Not owed, and not gone.** These are obligations that would ask if their
    subject were being worked. They are counted nowhere — not the badge, not
    the digest, not the fleet card — and rendered as one collapsed line so a
    reader can see what the rule decided and disagree with it in one click.

    Silence that cannot be opened is the complaint this whole phase answers,
    inverted. Each row carries the subject and the subject's status, which is
    the *reason*, so the line explains rather than merely counting.
    """
    return _walk(index)[1]


def _walk(index: "Index") -> tuple[
    dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]
]:
    """One pass over the corpus yielding **owed** and **suppressed** rows.

    One walk, deliberately, and now over one predicate for both answers:
    `counts_by_kind` used to walk separately and be asserted equal, which is a
    property that has to be maintained. Derived, it cannot drift.
    """
    owed: dict[str, list[dict[str, Any]]] = {v: [] for v in VIEWS}
    quiet: dict[str, list[dict[str, Any]]] = {v: [] for v in VIEWS}
    for path in index.paths():
        record = index.get(path)
        if record is None or not record.note_type:
            continue
        if record.rel_path.startswith("__templates__/"):
            continue
        ob = for_type(record.note_type)
        if ob is None or not ob.owed:
            continue
        view = view_for(record, ob)
        if not view:
            continue
        # Owed under the type's own declaration, before the subject is asked
        # about — so `deferred` and a non-owed status never reach the rule.
        if not _is_owed(record, ob):
            continue
        row = {
            "id": record.note_id or "",
            "title": record.title or "",
            "rel": record.rel_path,
            "type": record.note_type,
            "status": record.status or "",
            # The verb is the registry's, never the surface's — TASK-0357's
            # rule, and the reason `Approve` and `Triage` do not become
            # "resolve" in one pane and "handle" in another.
            "verb": ob.verb,
        }
        if record.note_type in SUBJECT_FIELDS and not subject_is_in_flight(
            record, index,
        ):
            quiet[view].append({**row, **_subject_detail(record, index)})
            continue
        owed[view].append(row)
    for view, rows in note_less_rows(index).items():
        owed[view].extend(rows)
    for bucket in (owed, quiet):
        for rows in bucket.values():
            rows.sort(key=lambda r: (str(r["type"]), str(r["id"])))
    return owed, quiet


def _subject_detail(record: Any, index: "Index") -> dict[str, Any]:
    """Why a row is quiet: the subject it names, that subject's status, and
    the phase it sits in — the phase for GROUPING only, never for the rule
    (ADR-0028 decision 4)."""
    subjects: list[dict[str, str]] = []
    phases: list[str] = []
    for note_id in subject_ids(record):
        path = index.by_id(note_id)
        subject = index.get(path) if path is not None else None
        if subject is None:
            continue
        subjects.append({"id": note_id, "status": subject.status or ""})
        raw = str(subject.frontmatter.get("phase") or "")
        for found in _SUBJECT_ID_RE.findall(raw):
            if found not in phases:
                phases.append(found)
    return {
        "subjects": subjects,
        "phases": phases,
        "reason": "no feature in flight",
    }


def counts(index: "Index") -> dict[str, int]:
    """Owed items per view — what each badge shows.

    Absent rather than zero is the renderer's job; this reports the truth and
    lets the surface decide what silence looks like.

    Derived from :func:`counts_by_kind` rather than counted separately: two
    passes over the same rule is how the total and the breakdown would come to
    disagree, which is the exact failure `badges_payload` exists to prevent.
    """
    return {view: sum(kinds.values()) for view, kinds in counts_by_kind(index).items()}


def badges_payload(index: "Index") -> dict[str, Any]:
    """The per-view counts plus the total, so a surface can assert on both.

    `total` is not decoration: ADR-0020 decision 3 says the badges must cover
    **every** kind, and a total that disagrees with the sum is how a kind goes
    missing without anyone noticing.
    """
    detail = counts_by_kind(index)
    per_view = {view: sum(kinds.values()) for view, kinds in detail.items()}
    return {
        "views": per_view,
        # Per view, `{kind: n}` for the kinds actually owed there right now
        # (ISS-0133) — so a badge can say `4 · requirements to approve` rather
        # than `4 items here need a person`, which was every view's tooltip.
        "breakdown": {view: kinds for view, kinds in detail.items() if kinds},
        # The verb each kind is owed, so the surface names the ACTION and does
        # not re-derive a vocabulary the registry already owns.
        "verbs": {
            note_type: ob.verb
            for note_type, ob in OBLIGATIONS.items() if ob.owed and ob.verb
        } | {src.kind: src.verb for src in NOTE_LESS.values()},
        # `{kind: [singular, plural]}` — the noun the badge says. Shipped so
        # the renderer picks a string rather than owning a plural rule.
        "nouns": {kind: list(pair) for kind, pair in KIND_NOUNS.items()},
        "total": sum(per_view.values()),
        "kinds": sorted(owed_kinds()),
    }
