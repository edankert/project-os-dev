---
type: "[[reference]]"
title: "What changed on <platform> since <tag>"
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
# The release tag these lines were written against. The release test uses
# them only while this is the last release tag for the platform; otherwise it
# prints the change notes' Impact sentences and says the lines are out of date.
tag: ""
---

# What changed on <platform> since <tag>

<Written at release preparation by the `release-test-prep` skill, one file per platform, saved as `docs/tests/acceptance/release-test/what-changed-<platform>.md`. One line per change and screen: the screen, a colon, one short sentence of at most 25 words about what a person sees now, and the change note it summarises. The release test prints each line under its screen, in the section that tests that screen. `release-test.py --check` warns about a change since the tag with no line here.>

- [[SUR-0000]]: <what the screen now shows, in a person's words> ([[CHG-YYYYMMDD-Short-Description]])
