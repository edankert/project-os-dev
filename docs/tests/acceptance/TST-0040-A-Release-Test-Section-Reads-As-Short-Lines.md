---
type: "[[test]]"
id: TST-0040
aliases: ["TST-0040"]
title: "A release test section reads as short lines: what changed for this platform, setup folded away, and numbered checks of one action and one expected line"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
scope: feature
level: acceptance
entrypoint: ""
command: ""
last_verified: ""
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
issues: []
tasks: ["[[TASK-0195]]"]
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
review_round: ""
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform]]", "[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]", "[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]"]
area: "Release test"
after: []
---

# A release test section reads as short lines

## Purpose

Confirms that the template produces the page Edwin approved on 2026-09-27, for Your Trainer's Equipment section on Android.

## Setup

A copy of your-trainer that has taken the template sync and run the migration script, with the Equipment section's procedure and test notes rewritten (your-trainer FEAT-0129, the rewrite of the procedures and test notes with the Equipment section pilot). The cheapest way: check out that branch in a scratch folder.

## Steps

1. Generate the Android release test for the open release and open the Equipment section.
2. Read the "What changed" part.
3. Open the setup.
4. Read the checks from first to last.
5. Run the length check on the Android platform.
6. Generate the iOS release test and open the same section.

## Expect

- Changes are listed under screen headings, one line each, and none is iOS-only.
- Setup has three parts: On the bench, Before you start, and Later, which names check numbers.
- Checks are numbered from 1. Each has one action line, one expected line and a TST tag.
- No expected line starts with "Step".
- Each group's start state appears once, and again only after skipped checks.
- The length check reports nothing for this section.
- No Android-only expected line appears on the iOS page.

## Not this check

- How the cockpit draws the page, marks results or shows progress. That is checked in project-os-cockpit.
- Whether the checks themselves pass on the app. That is Your Trainer's own release test.
