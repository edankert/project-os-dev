---
type: "[[task]]"
id: TASK-0054
aliases: ["TASK-0054"]
title: "Validator: collapsed ALLOWED_STATUS and a status check that reaches registered notes' frontmatter"
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
related: [ISS-0009, REQ-0016]
tests: []
---

# Validator: collapsed taxonomy

## Definition of Done

- [ ] `ALLOWED_STATUS` in `validate-docs.py` matches the collapsed `STATUSES.md`.
- [ ] The status check inspects **registered** notes' frontmatter, closing the gap described in [[ISS-0009-Fleet-Status-Vocabulary-Drift|ISS-0009]].
- [ ] `NOTE-STATUS` carries a cutover date per [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] rather than the current open-ended "graduate once migrated" comment.
- [ ] `load_allowed_status` still honours a repo's own `STATUSES.md` override — per-repo customisation is documented behaviour and is not being removed.
- [ ] Fixture covers: legal value, illegal value on a registered note, illegal value on an unregistered note, and a repo-level override.

## Steps

- [ ] Update `ALLOWED_STATUS` from TASK-0053's table.
- [ ] Extend checking to registered notes (see Notes for the precise hole).
- [ ] Add the `NOTE_STATUS_GATE_FROM` cutover constant following the `FEATURE_REQ_GATE_FROM` pattern.
- [ ] Build the fixture; confirm each case reports exactly once (no double-reporting from both the registered and unregistered paths).

## Notes

**The hole to close.** `validate_unregistered_notes` deliberately skips anything in `SNAPSHOT.yaml` (`if the_id in registered: continue`), on the stated grounds that registered notes are "covered by STATUS-VALUE / ITEM-STATUS against the snapshot entry". But `STATUS-VALUE` checks `entry.get("status")` — the *snapshot's* value — not the note's frontmatter. A registered note whose frontmatter holds an illegal value passes whenever its snapshot entry holds a legal one. So the 164 reported findings are a floor, not a census.

**Sequencing.** This lands before TASK-0055 so the validator can verify the migration rather than the migration being trusted. Note the interaction with [[FEAT-0015-Derived-State|FEAT-0015]]: once the snapshot is generated from frontmatter, snapshot and note status cannot diverge and this whole class of gap closes structurally — this fix is still needed in the interim, and should be written so it does not become dead code afterwards.
