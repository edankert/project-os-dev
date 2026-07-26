---
type: "[[plan]]"
status: done
parent: "[[FEAT-0016-Executable-Verification]]"
implements: [REQ-0022, REQ-0023]
related: []
---

# Plan: Executable verification

Template changes land in `~/Dev/repos/project-os`. The runner is rolled out read-only first (`--dry-run`, reporting what it *would* stamp) so the size of the hidden failure population is known before any note is rewritten.

- [ ] [[TASK-0066-Test-Command-Schema|TASK-0066]] — `command:`/`last_run:`/`last_verified:`/`waiver_expires:` in template + SCHEMAS.md + test-authoring
- [ ] [[TASK-0067-Test-Runner|TASK-0067]] — run-tests.py stamps status from execution; hand-edit becomes an error
- [ ] [[TASK-0068-Staleness-And-Waiver-Expiry|TASK-0068]] — staleness finding + expired-waiver error

## Dependencies

- **Hard:** TASK-0066 blocks TASK-0067 and TASK-0068.
- **Soft:** [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]] settles the test vocabulary (`passing`/`failing` only); doing this first would mean touching the same template twice.
- **Soft:** the promotion of any new check to error is governed by [[FEAT-0017-Enforcement-Severity|FEAT-0017]] clause 3 — debt cleared first.

## Open questions

- **Where does a command run?** Repo root is the obvious default, but tests that need a virtualenv, a device, or credentials will fail for environmental reasons and be indistinguishable from real failures. Minimum viable answer: a non-zero exit is `failing`, an *unrunnable* command (missing binary, missing env) is a distinct third outcome that reports as a finding rather than stamping `failing`.
- **Backfill of the existing 80 TST notes.** Most have no command. Do they become manual-with-`last_verified` set to their creation date — which would immediately mark most of them stale — or is the clock started at migration? Starting the clock at migration is kinder and less honest; TASK-0068 decides and records why.
- **48 existing waivers need expiry dates.** Assigning them uniformly is arbitrary; assigning them individually is 48 judgements. Consider expiring them all at a single near date and letting renewal be the forcing function.
