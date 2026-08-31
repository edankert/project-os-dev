---
type: instruction
id: INSTR-WRITING
status: active
owner: group:maintainers
created: 2026-08-31
updated: 2026-08-31
tags: [instructions, writing, clarity, prose]
---

# Writing rules (prose a reader can follow)

`MARKDOWN.md` covers how prose is **formatted**. This file covers whether it can be **understood**.

Scope: everything written for a human — chat replies, commit messages, and the prose inside notes (issues, features, tasks, changes, decisions).

## The failure mode is compression, not length

An agent that knows a codebase well packs a paragraph of meaning into a four-word phrase, invents a private vocabulary for the project, and puts the conclusion three paragraphs down. Every sentence is accurate, and every one costs the reader a decoding step.

Steven Pinker calls this the *curse of knowledge*: once you have chunked an idea into a label, you forget that the reader has not. Reported here by a maintainer on 2026-08-31, echoing more than one reader — "a lot of terminology at a very high level of abstraction, which makes it very difficult to understand".

## Rules

1. **Point first.** The first sentence says what changed and who notices it. Background comes after. This is the military "bottom line up front" convention, and it applies to a commit subject, a note heading, and the opening line of a reply.
2. **One idea per sentence.** Split at every em-dash and at every "which". A sentence over about 25 words is two sentences wearing one hat.
3. **Concrete subject, real verb.** Something a reader can point at does something. Not "the platform scoping stops at the derived view" but "the release page still lists platforms nobody tested on". Watch for abstract nouns built out of verbs — *scoping, migration, filtering, declaration, enforcement*. They eat the verb and hide who is acting.
4. **Gloss every invented term on first use**, in six words or fewer. "Mutation testing (break the code on purpose, check that a test fails)". If a compound word was coined for this project, it needs a gloss or a plain replacement.
5. **Name what the reader sees before the code symbol.** "The checks page reloaded twice" and then `repaintChecksPage`, never the reverse. A function name is evidence, not narration.
6. **No slogans as headings.** A heading like "Discriminating, not merely red" only parses for someone who already knows the point. State the fact, then the rule.

## Worked examples

| Instead of | Write |
| --- | --- |
| Two walker-facing fixes, guarded behaviourally rather than by grep | Two bugs Edwin hit while walking through a release. The new tests run the real code instead of searching the source for a function name. |
| The picker was doing two jobs: filtering the navigator AND declaring the platform a verdict was earned on, returning '' on All. | One dropdown controlled two things at once: which checks the list shows, and which platform gets recorded when you mark a check. Picking "All" recorded a blank platform. |
| Every renderer guard in that change set is a source-text grep, so it pins the spelling of a call site rather than the behaviour. | Those tests search the source code for a function name. They check that the name is still spelled the same way, not that the screen still works. |
| Discriminating, not merely red. | The test fails for the right reason, not just any reason. |

## Self-check before sending

- Read only the first sentence. Does it stand alone?
- Would someone who joined this project today get through the paragraph without asking what a word means?
- Is every subject something that exists — a person, a screen, a file — rather than an abstraction?

## What this does not mean

It does not mean dropping precision, avoiding technical terms, or writing for a beginner. Technical terms are fine; undefined ones are not. Detail is fine; detail with the conclusion buried under it is not.

Plain prose is usually **longer** than the compressed version. That is the correct trade: brevity bought with the reader's comprehension is not a saving.
