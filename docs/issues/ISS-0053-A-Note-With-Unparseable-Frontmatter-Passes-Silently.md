---
type: "[[issue]]"
id: ISS-0053
aliases: ["ISS-0053"]
title: "A note with unparseable frontmatter passes validation silently"
status: fixed
phase: "[[PHASE-0003]]"
severity: high
owner: user:edwin
created: 2026-09-04
updated: 2026-09-25
component: tooling
source: ["Found by the independent review of REQ-0027, 2026-09-04, which noticed ISS-0048's own frontmatter had been corrupted and nothing reported it"]
reported_by: review
related: ["[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]"]
tasks: []
tests: ["[[TST-0025]]"]
---

# A note with unparseable frontmatter passes validation silently

## Problem

A note whose YAML frontmatter does not parse drops out of every frontmatter-driven check and the validator says nothing at all — no error, no warning. Its status stops being checked, its links stop resolving, and the run still ends `validate-docs: OK`.

This is not hypothetical. `ISS-0048`'s frontmatter was corrupted on 2026-09-04 in commit `00b4fd8`: a bad string edit turned `related:` into `elated:` and dropped a closing quote. The note then sat through eight subsequent validator runs, four `sync-snapshot.py` runs, and a pre-commit hook, all green. It was found by a person reading the file, not by the tooling.

The blast radius is every check keyed on frontmatter. A note can carry any status, any links, or none, and be invisible.

## Repro

```bash
cd ~/Dev/repos/project-os-dev
cp docs/issues/ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them.md /tmp/x.bak
python3 - <<'PY'
p="docs/issues/ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them.md"
s=open(p,encoding="utf-8").read()
open(p,"w",encoding="utf-8").write(s.replace('related: ["[[ISS-0048', 'related: ["[[ISS-0048x, "[[ISS-0048',1))
PY
bash tools/scripts/validate-docs.sh | tail -1     # validate-docs: OK
cp /tmp/x.bak docs/issues/ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them.md
```

A second, quieter variant: renaming a known key (`related:` to `elated:`) parses fine and is also unreported, so a note can silently lose its whole link graph without any syntax error at all.

## Expected

A note under `docs/` whose frontmatter does not parse is an error, naming the file and the parser's message. A note missing a required key is at least a warning.

## Actual

Both are silent. `validate-docs: OK`.

## Evidence

- `docs/issues/ISS-0048-...md` as committed in `00b4fd8`: `elated:` on line 14 with an unterminated string.
- The repro above, run 2026-09-04 against `ISS-0050`.

## Next Actions

- [ ] Report a parse failure as an error, with the file and the YAML message.
- [ ] Decide whether an unknown top-level key warrants a warning. It catches the `elated:` class, and it risks noise in repos that carry their own fields, so measure across the fleet first.
- [ ] Check whether the cockpit's bundled validator has the same hole; it is a separate implementation ([[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]]).

## Sibling search

Sibling found: [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]], the other mechanical checks decided under ADR-0026. Filed separately and at higher severity because this one hides arbitrary other defects rather than being one class of defect. Searched `docs/issues/` for: frontmatter, YAML, parse, silent.

## Risk scan

One hazard: turning parse failure into an error could break a downstream repo that already has a corrupt note. That is the point of the check, but it should be measured across the fleet before it errors rather than warns (`STATUSES.md`, "Grandfathering").

## Checked against the template, 2026-09-18: still true

**What someone notices:** A note whose `related:` key is misspelled loses all its links, and the validator still says OK.

The first half is done: NOTE-FRONTMATTER reports frontmatter that does not parse (d2f78bc), and it fires here today on TST-0003 and CHG-20260804. Nothing checks top-level key names on notes.

**Next:** Narrowed to the second half: warn on an unknown top-level key, after measuring how many the fleet has.

Checked as part of FEAT-0036 (TASK-0140).

## Tasks, 2026-09-25

Edwin asked for PHASE-0003 to be completed and tested in full. The remaining work is [[TASK-0163]].

## Resolution, 2026-09-25

- **A parse failure is reported.** NOTE-FRONTMATTER (template, 2026-09-18, ported from project-os-cockpit) parses each note's frontmatter with PyYAML and names the file and the error. It warns until 2026-12-17, then errors (ADR-0011 clause 3). The repro above, run on a copy of this repo, is reported.
- **A misspelt link field is reported.** FRONTMATTER-TYPO ([[TASK-0163]]): a key no template or SCHEMAS.md defines, one or two letters from a field that carries links, is an error naming the field it resembles. `elated:` is caught. The wider rule this issue first proposed, any unknown key near any known key, was measured and rejected: about 50 findings over 8,668 notes, nearly all legitimate project fields.
- **The cockpit's validator does not have the hole.** All three copies carry NOTE-FRONTMATTER, and the repro is reported by it too.

Tested by [[TST-0025]]. Stays a warning for the parse check until 2026-12-17, as that check's own promotion date sets.
