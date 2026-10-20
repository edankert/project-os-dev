---
type: "[[issue]]"
id: ISS-0110
aliases: ["ISS-0110"]
title: "A finished phase is closed without anyone being shown what it changed, and a release reaches riders as a block of text; both should come from one generated showcase"
status: open
phase: ""
owner: user:edwin
created: 2026-10-20
updated: 2026-10-20
source: ["Edwin, 2026-10-20, in your-trainer: 'as part of SCRUM, the team does a sprint review, in which they show case all the functionality added in the sprint for the different stakeholders to provide some input ... that would be good to introduce here as well, when a phase is completed that we should have a phase review in which the LLM show cases all the changes?'", "Edwin, 2026-10-20: 'yes, record it upstream'", "Edwin, 2026-10-20: 'I am thinking now that actually that release-notes are a little old fashioned, can we turn this phase/review and new test infrastructure in a more interactive/visually appealing release note, not just for beta testers but for everybody?'"]
reported_by: agent
question: "Should the template add a phase review, generated when a phase's exit criteria are met and closed by the owner's verdict on each item, and should the same data produce a public release page in place of a text release note?"
severity: medium
component: "skills"
parent: ""
related: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]", "[[ISS-0109-The-Release-Test-Should-Be-A-Script-An-App-Can-Run]]"]
tests: []
---

# A finished phase has no review, and a release has only a text note

## Problem

A phase closes when its exit criteria are ticked. Nobody is shown, in one place, what the phase changed. The owner learns it piece by piece, from task notes and from the release test.

A release reaches riders as a short text note in the store, and sometimes as a Discord post. Neither shows a picture of what changed.

The template already holds the material for both:

- the phase note and the features and tasks that name it;
- the change notes, whose Impact lists name each screen a change altered;
- the screen galleries, with git holding each earlier picture;
- the tests added, and the results in the release ledgers.

## Expected

### 1. A phase review, for the owner

When a phase's exit criteria are met, a `phase-review` skill and script build a review note under `docs/reviews/`, and the cockpit opens it. The note has one section per feature the phase delivered:

- what changed, in two or three plain sentences, starting with what a user notices;
- before and after for each screen it changed, on every platform side by side, taken from the galleries at the phase's first and last commits;
- a short recording where motion matters, once the app's UI tests can drive the screen;
- how it was checked: the tests that now guard it, what a person tested, and anything untested;
- what is left: deferred items, open questions and issues found;
- the owner's verdict: Accept, Change or Drop, with a comment. A Change or a Drop becomes an `ISS-*` at `status: triage` for the next phase.

"Phase review held, verdict recorded" becomes a standard exit criterion in the phase template. An item the owner does not answer within a set number of days counts as accepted, as on the taste page in your-trainer ADR-0020.

### 2. A release page, for everybody

The same data, cut to what the owner accepted and rewritten for users, becomes a release page in place of a text release note:

- one card per change, with a headline written with the product as the subject, a before-and-after picture with a slider, and a short looping clip where motion matters;
- in every language the app ships, with screenshots taken in that language where the screenshot tool can do it;
- a static page with no analytics, because the apps that use this template promise not to phone home;
- the store's "What's new" text generated from the same cards, short enough for the store's limit, with a link to the page;
- a Discord or newsletter post generated from the same cards.

An app may also bundle the same cards and show them once after an update, as an in-app "What's new". That is each app's own choice, because it is a new screen users see.

## What each app writes

The template generates the review and the release-page data. Each app supplies its galleries, its recordings, and, if it wants one, its in-app "What's new" screen.

## Notes

- This is the end of a chain that ISS-0108 and ISS-0109 start. ISS-0108 cuts the checks a person owes, ISS-0109 lets an app run the ones left in one guided session, and this issue shows the owner and then the users what the work produced.
- your-trainer's release ride (FEAT-0140) draws a step card over the app's real screens. The same card could carry an in-app tour of what changed for users.
- The cockpit's Accept, Change and Drop buttons are cockpit work, and they would be filed in project-os-cockpit when this is taken up.
