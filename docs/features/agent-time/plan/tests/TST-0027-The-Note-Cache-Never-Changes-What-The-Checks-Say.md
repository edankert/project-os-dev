---
type: "[[test]]"
id: TST-0027
aliases: ["TST-0027"]
title: "The note cache re-reads a changed note, distrusts a changed validator, and never changes what the checks report"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0169]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-note-cache.sh"
command: "bash ../project-os/tools/scripts/test-note-cache.sh"
covers: ["[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]"]
tasks: ["[[TASK-0169]]"]
issues: ["[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 11 assertions, with and without PyYAML. Four mutations in a scratch copy: M1 the key ignores mtime, 1 failure; M2 the cache tag ignores the validator's own text, 1; M3 a corrupt cache file is believed, 3; M4 the index drops body links, 2. Pristine 11 of 11."
related: []
---

# The note cache re-reads a changed note, distrusts a changed validator, and never changes what the checks report

## Purpose

TASK-0169 made the validator, `walk-sheet.py` and `sync-snapshot.py` parse each note once and keep the result on disk between runs. A stale cache would make the checks report on a note as it used to be. This test pins down when the cache may answer and when it must re-read.

## Procedure

`bash tools/scripts/test-note-cache.sh` in `~/Dev/repos/project-os`. The cache lives under a private `TMPDIR`. A helper can make the real parser raise, so an answer given anyway must have come from the cache.

- `PROJECT_OS_NO_CACHE=1` parses and writes no cache file.
- A first run writes one; a second answers from it, with the value's type kept (a date stays a date under PyYAML).
- An edit that keeps the note's size is re-read, because the mtime is in the key; an edit that changes the size is re-read.
- A copy of the validator with one changed line does not trust the old cache.
- A corrupt cache file is ignored.
- `note-index.py` gives a note's id, status, path, links (frontmatter and body) and headings; `--links-to` inverts the links; an unknown id exits 1.
- The validator's output on the template's own notes is identical with the cache off, cold and warm.

## Expected results

- Exit 0: 11 of 11, 2026-09-26, and the same with PyYAML hidden.

## Fleet evidence, 2026-09-26

Validator output with the cache off, warm and warm again was identical on all 13 fleet repos, and identical to the validator as committed before the change (`project-os` HEAD `ca29288`). `sync-snapshot.py --check` and `walk-sheet.py --check` gave the same output and exit code with the cache off and on in all 13.
