---
type: "[[requirement]]"
id: REQ-0007
aliases: ["REQ-0007"]
title: "Risk scans must be mandatory with explicit trigger checklist"
status: implemented
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
priority: high
implements: ["[[FEAT-0005]]"]
acceptance:
  - "Close-out, feature-scaffold, and issue-intake skills each include a risk scan step bound to the canonical trigger checklist"
  - "The trigger checklist is explicit and single-sourced in LIFECYCLE.md (mirrored in the risk-scan skill), referenced by each skill rather than duplicated"
  - "Agent must create RISK-* note if any trigger applies, or record 'No new risks identified'"
related: [ADR-0004]
---

# Risk scans must be mandatory with explicit trigger checklist

## Acceptance Criteria

- [x] Close-out, feature-scaffold and issue-intake all include a risk-scan step bound to the canonical trigger checklist — evidence: `close-out/SKILL.md` step 6, `feature-scaffold/SKILL.md` step 8, `issue-intake/SKILL.md` step 8, each directing the scan against the triggers in `LIFECYCLE.md`.
- [x] The trigger checklist is explicit and single-sourced — evidence: the five triggers (new dependency, env/config surface, path/layout change, performance, security/credential/licence) appear in `tools/instructions/LIFECYCLE.md` "Risk scan triggers" and are mirrored in `tools/skills/risk-scan/SKILL.md`; skills reference it rather than duplicating it per skill.
- [x] A `RISK-*` note is created when a trigger applies, or the negative result is recorded — evidence: the "if no trigger applies, record that no new risks were identified" clause is now present in all three skills (previously only in close-out).

## Amendments (2026-07-21)

**Criteria 1 and 2** were reconciled. As written they required each skill to carry its *own inline* trigger checklist; the delivered design single-sources the checklist in `LIFECYCLE.md` (mirrored in the risk-scan skill) and has each skill reference it — deliberately, so the trigger list cannot drift between four copies. Criteria rewritten to describe the reference model.

**Criterion 3** was genuinely incomplete: only `close-out` carried the "record the negative" clause, so a feature-scaffold or issue-intake run with no triggers left no evidence the scan happened. Closed by adding the clause to `feature-scaffold/SKILL.md` step 8 and `issue-intake/SKILL.md` step 8 rather than narrowing the criterion.

Known limitation, deliberately not part of this requirement: the HC-005 hook (`risk-scan-trigger.sh`) is advisory-only (always exits 0) and the validator has no risk-scan check, so risk scanning remains convention-enforced rather than mechanical.

