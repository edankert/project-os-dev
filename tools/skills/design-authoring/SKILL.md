---
type: skill
id: SKILL-DESIGN-AUTHORING
status: active
owner: user:edwin
created: 2026-07-27
updated: 2026-09-12
tags: [skills, design]
---

# Skill: Design authoring

## Why this exists

A design has to be **looked at**. This says where the pictures go, so that a reader sees them in Obsidian, in the cockpit and on GitHub rather than in one of the three.

**Rewritten 2026-09-12.** This skill used to open with *"The artifact is HTML, and self-contained"*, and everything below it — regions, tokens, viewports — served an HTML file framed by the cockpit's design bench. That bench is being removed (project-os-cockpit ADR-0042, ADR-0043, REQ-0065), and the rule it taught produced this: `your-health`'s DES-0002 was a **4.6 MB HTML file carrying 51 base64 PNGs**, because an HTML artifact could not reference an image file beside it, and because the contract said a design is an HTML file. The pictures were always the design; the file was the wrapping.

## When to use

Before authoring or revising any `[[design]]`.

## A design is Markdown with pictures

Write the note. Put the images in `__attachments__/` beside it. Reference them with a **relative path**:

```markdown
![Plate 3 — the dial replacing the ring](__attachments__/plate-3-dial.png)
```

That renders in Obsidian, in the cockpit and on GitHub. Nothing else you can write does all three.

Caption every picture in the line beneath it. A screenshot nobody labels is one the reader has to interpret, and their interpretation is where the review goes wrong.

`asset:` in the frontmatter is **optional and usually empty**. A design with pictures in it and no `asset:` is complete, and the validator agrees: `DESIGN-ASSET` asks for *something to look at*, which pictures satisfy.

## When an HTML page earns its keep

Write one only when the design needs something a picture cannot carry:

- **Live layout** — the reader must resize it, or see it reflow at a real width.
- **Interaction** — a toggle, a hover state, a transition that a still cannot show.
- **Generated views** — many cases from one template, where hand-making the pictures is the error-prone part.

Otherwise a picture is better: it is smaller, it diffs as a binary that nobody pretends to read, and it renders everywhere.

If you do write one, it is a file beside the note, and the note links it like anything else. Keep it honest:

- **No network.** No CDN, no remote font, no fetch. The viewer frames it and a strict boundary applies; a page that needs the network renders broken and cannot be read offline.
- **Reference images as files beside it**, not as base64. A page and its pictures may share `__attachments__/`.
- **Assume no access** to the sidecar, the repo or the shell. A framed page is content, not code.
- **Scripts do not run in Obsidian**, which sanitises them, so anything script-driven is cockpit-only by nature.

## HTML inside a note

You may write HTML directly in a note body — both Obsidian and the cockpit render it (project-os-cockpit ADR-0043). There is no marker and no fenced block: a fence shows source, which is what a fence is for. Four rules come with it, and they are in `../../instructions/OBSIDIAN.md`, the shortest of which is the one that bites: **a picture inside raw HTML does not display in Obsidian** — use a Markdown image.

## Revisions are commits

The rule is `../../instructions/TRACEABILITY.md`, "`[[design]]` links": one design per commit, with the reason in the message. Not six edits and one commit at the end.

Images diff as noise, so the commit message and the note's `## Revisions` line are the only readable record of *why* anything changed.

## Checklist

- [ ] The pictures are in the note, in `__attachments__/`, referenced by relative path
- [ ] Every picture has a caption saying what it shows
- [ ] `asset:` is empty unless an HTML page earns its keep by one of the three reasons above
- [ ] A page, if there is one, makes no network request and references its images as files
- [ ] The note opens with the problem, not the solution
- [ ] Committed alone, with the reason in the message

## Starting points

Scaffolds by *section*, not by platform. A design opens with the problem, not the solution:

**A surface** — the states it must handle, including the empty and error cases, then the busy case. A surface designed only for the busy case usually looks broken, because quiet is the common state.

**A dossier** — one plate per decision, each stating the problem before the proposal, with the alternatives that lost. Number the plates stably so a comment can name one.

**A design system** (`role: system`) — use `docs/__templates__/design-system.md`. Same sections in every project, so two projects are comparable by diff.

## What was retired with the bench, and why it is not here

`data-design-region` annotation, the token-parity contract and `viewport:` all served bench machinery that was removed. Measured across the fleet on 2026-09-12, by the `type:` field and excluding template copies: **23 design notes in 8 repos, 21 of them declaring an HTML artifact — and against that, 7 artifacts declaring regions, 12 region-anchored comments in total (all on one note, from one reviewer, in one pass), one note using `## Variant`, and `chosen_variant` set on none.** A contract nobody exercises is a contract that teaches a false cost.

If a design still wants to name its parts — and a good one does — name them in prose, and let a comment quote the name.
