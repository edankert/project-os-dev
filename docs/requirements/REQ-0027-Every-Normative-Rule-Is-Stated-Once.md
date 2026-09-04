---
type: "[[requirement]]"
id: REQ-0027
aliases: ["REQ-0027"]
title: "Every normative rule is stated in exactly one file"
status: implemented
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: "2026-09-04"
priority: high
scope: "tools/instructions/, tools/skills/ and docs/__templates__/ in the project-os template, and the adapter outputs generated from them"
source: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]] option 1", "[[Prompting-Guide-Review-2026-09-03]] findings 1.1 to 1.3"]
acceptance:
  - "No normative rule in the scope is stated in two places that disagree. A rule with one home and links to it is the standard; a second copy that says the same thing is tolerated, and a second copy that says something different is a defect (user:edwin, 2026-09-04)."
  - "ISS-0041, ISS-0042 and ISS-0043 are resolved by deleting the restatement and linking, not by correcting another copy."
  - "The six criteria of REQ-0018 remain satisfied after the widening."
  - "The docs-audit skill names this rule as what its instruction/template-drift dimension checks, and the audit runs at each backlog-grooming pass and before each release."
  - "A mechanical check (RULE-ONCE) is decided or declined, recorded in ADR-0024's Acceptance section with the violation count that decided it."
implements: ""
supersedes: "[[REQ-0018-State-Rules-Stated-Once]]"
verifies: []
related: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0018-State-Rules-Stated-Once]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]]", "[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]"]
tests: []
reviewed_by: model:claude-fable-5-1
review_date: 2026-09-04
review_verdict: changes-requested
---

# Every normative rule is stated in exactly one file

## Statement

Every normative rule in project-os shall be stated in exactly one file. Every other document shall link to that statement rather than restate it. A restatement is a copy that the next amendment can miss, and four issues in fourteen months show that it does get missed.

This widens [[REQ-0018-State-Rules-Stated-Once|REQ-0018]] from state and transition rules to every normative rule. REQ-0018 was `implemented`, and a terminal requirement is not reopened, so this requirement supersedes it (ADR-0024, option 1). REQ-0018's six criteria stay in force through criterion 3 below.

## Acceptance Criteria

- [x] No normative rule in the scope is stated in two places that disagree — evidence: twelve sweep passes 2026-09-03/04 fixed 36 + 26 + 2 + 3 + 2 + 2 + 21 + 2 + 5 + 25 restatements (`1b5956e` to `e2bee28`), and the surviving duplicates were then classified one by one. Nine disagreed and are fixed in template `ef1f29f`: the sync script derives `goal:` where two documents said it does not (verified by rewriting a snapshot goal and watching the script restore it), `SNAPSHOT.md` on the two edges ADR-0032 removed, `requirements/README.md` on `implements:`, two READMEs turning a mandatory rule into a preference, `CONTEXT.md`'s edit policy against LIFECYCLE, two ID-prefix lists disagreeing with each other, the validator's `reference` default, and a terminal status inside an "Open" view. The copies that agree are left in place, which is what the narrowed criterion permits

- [x] ISS-0041, ISS-0042 and ISS-0043 are resolved by deletion and linking — evidence: template commits `1b5956e`, `685eef7`, `0049206` (2026-09-03), each deleting the copy and linking the home
- [x] The six criteria of REQ-0018 remain satisfied — evidence: rows 4, 8, 13 and 14 of ISS-0048 were the state and transition rules restated, and all four were fixed in template commits `ab94b0c` and `09ae4dc`. Re-checked on 2026-09-04 after passes 11 and 12: the status value lists live only in STATUSES.md, the three documents that had grown their own copies (`docs/STYLEGUIDE.md`, `docs/releases/README.md`, `docs/phases/README.md`) now link it, and `BASE-STATUS` enforces the same rule for the shipped views mechanically
- [x] The docs-audit skill names this rule and the audit runs on cadence — evidence: template commit `c5dc296` (2026-09-03) named the rule; `17edc84` (2026-09-04) replaced "to quiescence" with one bounded round per ADR-0026, and the criterion text above follows it
- [x] RULE-ONCE decided or declined — evidence: ADR-0024 "Acceptance", the second box: declined for now on a count of 36, 2026-09-03, with the reasons and the condition for reconsidering

## Amendments

**2026-09-04, criterion 1 narrowed by user:edwin (the owner).** It read "every normative rule has exactly one home file; every other document links to it rather than restating it". It now reads: no rule is stated in two places that *disagree*.

> [!quote] As decided — 2026-09-04 (user:edwin)
> How can we complete REQ-0027, do these duplicate rules contradict, if they do, that is definitely worth fixing if they don't then I am happy leaving them.

Why the original could not be satisfied: it is an absolute over a corpus that keeps changing, so it has the same shape as the quiescence rule [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] removed — twelve sweep passes fixed 124 restatements and the count never reached zero. An independent review on 2026-09-04 correctly refused a first attempt to tick it, because the residue on [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]] listed rules still stated twice.

What the narrowing keeps and what it gives up. It keeps the failure the rule exists to stop: an agent reading two files and being told two different things, which is what ISS-0006, ISS-0041, ISS-0042 and ISS-0043 all were. It gives up the tidiness argument — a second copy that agrees is now tolerated, and the risk is that it later drifts out of agreement unnoticed. That risk is what the cadence sweep and the checks under [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks|ISS-0052]] are for, and it is a smaller risk than a requirement nobody can ever satisfy.

## Why a requirement and not only the ADR

The ADR records the decision. The requirement is what a feature or an audit can be checked against, and what stays true after the four current issues close. Without it, the fifth restatement is filed as a one-off, which is the failure the intake harvest rule exists to catch.

## Traceability

- Decision: [[ADR-0024-A-Normative-Rule-Is-Stated-Once]]
- Supersedes: [[REQ-0018-State-Rules-Stated-Once]]
- Instances: ISS-0006 (fixed, July), ISS-0041, ISS-0042, ISS-0043
- Verified by: the docs-audit skill's instruction/template-drift dimension, run to quiescence

## Independent review (2026-09-04, model:claude-fable-5-1, clean context)

Verdict: **changes-requested**. Authored by model:claude-opus-5[1m]; reviewed by the same model family in a separate session with no authoring context, from the notes and the diff (commits `fcdba90`, `606f0ee`, `09290f6` here; `17edc84`, `ad61433` in the template). Family is shared; session and context are not (QUALITY.md, "Independent review").

**Blocking findings, each reproduced.**

1. **Criterion 1 is ticked against a criterion of record it does not meet.** The frontmatter `acceptance:` list, which the close-out skill says wins over the body, is byte-identical before and after `fcdba90` (`git show fcdba90 -- docs/requirements/`); it still reads "every normative rule in the scope has exactly one home file". The residue table on ISS-0048 records known restatements left in place (row 4: six directory READMEs carrying their own trigger lists; rows 2, 3, 13), and ISS-0048's pass-12 row says its 25 findings are "not yet fixed". What was reworded was the evidence clause in the body, not the criterion, and there is no `## Amendments` section. Criterion 4 in the frontmatter still requires the audit "run to quiescence", a rule ADR-0026 deleted, and the Traceability line still says "run to quiescence". This is the case QUALITY.md names: narrow the criteria in the frontmatter with recorded rationale, or leave the requirement at `approved`.
2. **`BASE-STATUS` is not committed in the template.** `git -C ~/Dev/repos/project-os show HEAD:tools/scripts/validate-docs.py | grep -c BASE-STATUS` prints 0; the check exists only as an uncommitted working-tree change (`git status` shows `M tools/scripts/validate-docs.py`). The CHG note lists `validate-docs.py` under `impacts:` against `commit: "17edc84"`, which touches only two skills. Criterion 3's evidence ("`BASE-STATUS` enforces the same rule for the shipped views mechanically") and ADR-0024's "built" therefore describe the implementation target's working tree, not anything landed. Both repos are also 28 commits ahead of `origin/main`, so LIFECYCLE close-out step 9 (a green CI run) has not happened for any of this.
3. **The evidence for the ADR-0026 amendment is confounded.** ISS-0048's passes table shows pass 11 ran at `19ba330` and was fixed in `acdcccb`, `7c13209`, `e2bee28`; pass 12 ran at `e2bee28`. Pass 12 therefore read a corpus from which pass 11's findings had already been removed, so "overlapped on almost nothing" is guaranteed by construction and says nothing about what two parallel passes at one commit would share. The retired-status views (fixed in `acdcccb`) could not have been a pass-12 finding. What the data does support is that a single pass misses real defects (ISS-0051 existed at `19ba330` and pass 11 did not report it). The ADR's Options section still defines option 5 as two-of-three agreement while `decided_option: "5"` and the decision text say union; the accepted text and the implemented rule now differ, and LIFECYCLE puts a real scope change with the user. Recommend the user confirm or revert the amendment and the ADR restate the evidence as what it is.
4. **Closing ISS-0048 `fixed` leaves nine residue rows with no open item.** Rows 1, 2, 3, 6, 7, 8, 12, 13 and 14 are marked Open and are filed nowhere; row 1 says "needs a decision", and the docs-audit skill written in the same commit says a decision owed becomes an `ISS-*`. Retention will prune the fixed item from the snapshot and `focus.note` is transient, so after that nothing at an open status carries these findings. The note survives, but the residue becomes invisible to every open-work view. Recommend one `ISS-*` at `triage` for the residue, linked from ISS-0048.
5. **ISS-0048's frontmatter is not valid YAML.** Line 14 reads `elated:` (not `related:`) and drops the closing quote after `[[ADR-0024-...]]`; `yaml.safe_load` fails with a ScannerError. Introduced in `00b4fd8`, carried unchanged through the closing edit; the validator's lenient parser reads past it, so the LINK check never sees the issue's relationships.

**Non-blocking findings.** (a) ADR-0026's acceptance box links `[[ISS-0052-Four-Drift-Classes-Should-Be-Checks-Not-Sweep-Findings]]`; the file is `ISS-0052-Three-More-Drift-Classes-Should-Be-Checks.md`, and LINK checks only frontmatter fields, so body wikilinks dangle unchecked. (b) ADR-0026's decision record has a third callout whose body is the single word "option". (c) The template docs-audit skill still says `updated: 2026-09-03` after the 09-04 rewrite, and its "Why this exists" still says systems "needed multiple full-scope audit rounds before converging", which the rest of the file now denies. (d) `BASE-STATUS` false negatives, reproduced by appending each form to `NAVIGATION.base` and running the wrapper: single-quoted literals, `status.contains("x")`, `["x"].contains(status)`, `status in [...]`, a second `==` on the same line, a `containsAny(` wrapped across lines, and a space before the paren all pass with a retired value; only `docs/__bases__/` is scanned, so `docs/__templates__/feature-overview.base` (tracked here) is never checked. Caught: `containsAny("a","b")`, `== "a"`, `!= "a"`, negated `containsAny`, `note.status`/`file.properties.status` prefixes. (e) "17 of 17 spot-checked" appears in three notes; only pass 12's "four of four" has a record, the other thirteen have none (not reproduced). (f) ADR-0026 counts 18 review verdicts (16/2); `grep -rho review_verdict docs` today counts 19 approved and 3 changes-requested. (g) `implements: ""`: STATUSES.md says a requirement is written `implemented` at feature close-out and the close-out skill says a requirement naming no feature is not advanced by one; REQ-0018 named FEAT-0014, this note names nothing.

Reproduction commands and outputs are in the review transcript; the parent transcribes what it accepts into `ISS-*` notes (independent-review skill, step 5).

