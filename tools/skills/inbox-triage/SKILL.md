---
type: skill
id: SKILL-INBOX-TRIAGE
status: active
owner: group:maintainers
created: 2026-07-28
updated: 2026-07-28
tags: [skills, intake, inbox, triage]
---

# Skill: Inbox triage

## When to use
- `inbox/` is not empty.
- The user drops, pastes, or otherwise leaves external material for the project — a screenshot, an export, a log, a page of notes.

That is the whole trigger. The inbox is **staging, and its success condition is being empty**, so a non-empty inbox is itself the reason to run this.

## What the inbox is
- **Pre-documentation.** Material that has arrived but has not yet been decided about.
- **Gitignored.** It is local staging, not a record. An agent in a fresh clone sees an empty inbox, and that is correct.
- **Not a filing cabinet.** Anything still sitting there is an unmade decision, not an archive.

## Inputs
- The files in `inbox/`.
- Whatever the user said when they left them, if anything. Often nothing — a screenshot arrives with no words at all.

## Outputs
- Content filed into the right notes, split across several, or turned into new ones — **and the inbox item removed**.
- Or the item discarded, deliberately.
- Either way: `inbox/` is empty when you are done, and the user knows what happened to each item.

## Steps

1. **Look at every item before deciding about any of them.** Two screenshots may be one story, and filing the first alone gets the second wrong.
2. **For each item, ask what it is evidence *of*.** A screenshot of a broken layout is evidence for an issue. A page of scribbled requirements is a feature or several. An export is usually reference. If you cannot say what it is evidence of, that is a question for the user, not a guess.
3. **Decide, and say which:**
   - **File it** — attach to an existing note, moving the artefact somewhere durable (e.g. `docs/<area>/assets/`) and linking it from the note that needs it.
   - **Split it** — one item can be evidence for several notes. Splitting is the normal case for anything hand-written, not an edge case.
   - **Create** — sometimes the honest home does not exist yet. Run the relevant intake skill (`issue-intake`, `feature-scaffold`) rather than inventing a note shape here.
   - **Discard** — a duplicate, a mis-drop, or something already captured. Deliberate discarding is a *good* outcome and must not be avoided out of caution.
4. **Handle the partly-useful item properly.** The hard case is not "keep or delete" — it is an item where one paragraph matters and the rest is noise. **File the useful part and discard the remainder.** Keeping the whole thing because part of it was useful is how an inbox becomes an archive.
5. **Remove the item.** Filing without removing leaves a copy in staging that will be filed again later.
6. **Report what happened to each item**, by name. The user dropped these deliberately; silently absorbing them means they cannot tell whether you understood.

## Guardrails
- **Never leave an item in the inbox** as a way of deferring the decision. If you genuinely cannot decide, ask — an unanswered question is a better record than an unexplained file.
- **Do not commit the inbox.** It is gitignored; keep it that way. What gets committed is the *filed* artefact.
- **Do not treat an inbox item as a source of truth.** It is unreviewed external material until you decide otherwise; the note you file it into is the record.
- **Do not paraphrase an image into a note and throw the image away** unless the words genuinely carry everything. A screenshot of a rendering bug *is* the evidence; a sentence describing it is not.
- Discarding is fine. Discarding **silently** is not — say what you dropped and why.

## Related
- `ad-hoc-intake` — the same decision applied to an unstructured *prompt* rather than an artefact.
- `issue-intake`, `feature-scaffold` — where an item ends up when the honest answer is "this is new work".
