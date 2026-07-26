---
type: "[[task]]"
id: TASK-0073
aliases: ["TASK-0073"]
title: "Cockpit: align the status vocabulary across eight surfaces; the delivered band empties"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0013-Status-Taxonomy-Collapse]]"
effort: M
due: ""
depends: [TASK-0053]
blocks: []
related: [ADR-0008, REQ-0016, REQ-0017]
external: "../project-os-cockpit/docs/issues/ISS-0025-Incoming-Taxonomy-Collapse.md"
tests: []
---

# Cockpit vocabulary alignment

## Definition of Done

- [ ] The collapsed vocabulary is reflected in all **eight** surfaces that enumerate it (see Notes), with `tests/test_status_vocabulary.py` green.
- [ ] **The `delivered` band's fate is decided and recorded**, because ADR-0008 deletes both of its only members (see Notes).
- [ ] `DONE_BY_TYPE` in `cockpit.py` updated for the merged issue terminal (`closed` → `fixed`).
- [ ] Legacy vocabulary is retained where it is deliberately tolerated for unmigrated repos, and that tolerance is documented rather than incidental.
- [ ] Released from `project-os-cockpit`, then propagated: `release-to-project-os.sh` → `project-os` (`tools/cockpit/`) → 9 downstream repos via sync. All three hops confirmed.

## Steps

- [ ] Wait for [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]] — the vocabulary must be settled first.
- [ ] Update `statuses.py` (the canonical `BANDS`), then let `test_status_vocabulary.py` name every surface that has fallen behind.
- [ ] Decide the `delivered` band question.
- [ ] Release and propagate all three hops.

## Notes

**The delivered band empties.** `statuses.py` documents it precisely: ISS-0023 created `delivered` for work shipped but not signed off; `implemented` was its founding member until ADR-0007 made that terminal, leaving the band with exactly two members — `staged` (release, verified but not live) and `monitoring` (risk, mitigated but still watched).

ADR-0008 deletes both: `staged` and `monitoring` were each written **zero times** across 5,890 fleet status writes. So the collapse does not shrink the band — it **empties it**, along with its exclusion from Hide-completed and its `STATUS_RANK` slots at 51/52.

Three options, to be decided rather than defaulted:

1. **Retire the band.** Honest — it has no members and never had a member anyone wrote. Unwinds ISS-0023 entirely.
2. **Keep `staged`/`monitoring` as an ADR-0008 exception**, on the same grounds `failing` is retained: unreachable rather than unwanted. Weaker here, because no planned work makes them reachable the way [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] makes `failing` reachable.
3. **Repopulate it** with something genuinely non-terminal from the collapsed vocabulary.

Option 1 is the default reading of ADR-0008, but it deletes a distinction the cockpit deliberately built ten months of reasoning into, so it deserves an explicit decision in the cockpit repo rather than falling out of a vocabulary edit upstream.

**Eight surfaces, not six.** The `statuses.py` docstring says six. The current count is eight: `statuses.py`, `cockpit.py`, `templates.py`, `validate_docs_bundled.py`, `static/cockpit.js`, `static/cockpit.css`, `static/base.css`, `desktop/src/renderer/renderer.ts`. The parity test is what makes this tractable — update the canonical table and let the test enumerate the stragglers.

**Verified not-broken today**: every status currently in project-os-dev (`accepted`, `active`, `backlog`, `cancelled`, `closed`, `done`, `draft`, `fixed`, `implemented`, `merged`, `open`, `planned`, `proposed`, `reference`, `superseded`, `triage`) maps to a band, and all three phases including `PHASE-999` resolve. This task is about the *planned* collapse, not a live defect.
