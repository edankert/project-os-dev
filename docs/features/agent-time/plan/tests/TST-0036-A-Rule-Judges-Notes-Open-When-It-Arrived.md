---
type: "[[test]]"
id: TST-0036
aliases: ["TST-0036"]
title: "A content rule does not judge a note finished before it arrived, and --changed shows only what changed while still failing on every error"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0179]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-rule-arrival.sh"
command: "bash ../project-os/tools/scripts/test-rule-arrival.sh"
covers: ["[[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed]]"]
tasks: ["[[TASK-0179]]"]
issues: ["[[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 9 assertions. Five mutations in a scratch copy: M1 no filter, 2 failures; M2 open notes filtered too, 1 (survived until the judge got its own check); M3 every finished note hidden, 3; M4 --changed shows everything, 1; M5 --changed exits on the shown errors only, 1 (survived until a run had only a hidden error). Pristine 9 of 9."
related: []
---

# A content rule does not judge a note finished before it arrived, and --changed shows only what changed while still failing on every error

## Purpose

ISS-0094: rules added after a note closed kept reporting on it every run. ADR-0048 decided a content rule judges only notes still open when it arrived.

## Procedure

`bash tools/scripts/test-rule-arrival.sh` in `~/Dev/repos/project-os`, on a copy of the template in its own git repo, so REQ-BOXES arrives on the fixture's first commit.

- An implemented requirement last touched in January gets no REQ-BOXES finding; one touched after the rule arrived does. The hidden finding is counted, by rule.
- A frontmatter parse error on the old requirement is still reported: structural checks judge every note.
- `--changed` shows the finding about the edited note, hides and counts the one about an unchanged note, and still exits 1 on it, including when the hidden error is the only one.
- The judge keeps an open note whatever its date, and never filters a rule with no arrival date.

## Expected results

- Exit 0: 9 of 9, 2026-09-26.
