---
type: skill
id: SKILL-DESIGN-AUTHORING
status: active
owner: user:edwin
created: 2026-07-27
updated: 2026-09-03
tags: [skills, design]
---

# Skill: Design authoring

## Why this exists

The cockpit's design bench ships detectors — region annotation, palette parity, asset resolution — and the first real artifact satisfies **none** of them. Measured on `DES-0001`, a 139KB dossier:

- **zero** `data-design-region` declarations, so annotation has nothing to anchor to
- tokens named `--m-done`, `--t-feature`, `--m-accent` against an implementation saying `--status-done`, `--severity-critical`, `--accent-link`
- `--m-accent:#3b6ea8` where the implementation has `hsl(212 48% 42%)` (≈`#386ba0`), in a block the dossier labels *"cockpit tokens, verbatim"* — already false when written

Detectors without a contract fire on everything and mean nothing. This is the producer half.

## When to use

Before authoring or revising any `[[design]]` artifact.

## The artifact is HTML, and self-contained

One file. No CDN, no external stylesheet, no remote font, no network fetch. The cockpit frames it and a strict boundary applies; an artifact that needs the network renders broken and cannot be reviewed offline.

Scripts **are** allowed — `DES-0001` carries a theme toggle and it is legitimate. Assume the frame gives you no access to the sidecar, the repo, or the shell: an artifact is content, not code, and behaving as though it were is how a design surface becomes an attack surface.

## Declare regions

Every part a reviewer might comment on carries one:

```html
<section data-design-region="focus-band"> … </section>
```

**IDs are unique within the artifact.** A dossier with five plates has five focus bands, so scope them (`plate-c-focus-band`), never repeat a bare `focus-band`.

Two rules that follow from how annotation works:

- **A region that is not declared cannot be commented on.** Name anything a reviewer might object to, which is a wider set than the parts you want to point at. Author pins mark what *you* think matters; regions must cover what *they* might.
- **Renaming a region orphans its comments** — indistinguishable from delete-and-add. Treat a region ID as a published name: add and deprecate, do not rename.

Some criticism has no region — *"too much violet everywhere"*, or a complaint about the relationship between two areas. Those land in the note's document-level lane. Do not invent a region to host them.

## Declare tokens

If the design specifies values the implementation must match, use **the implementation's token names verbatim**:

```css
:root { --status-done: hsl(160 28% 38%); }   /* not --m-done */
```

If you cannot — the artifact needs its own chrome, or you are illustrating rather than specifying — declare the mapping once in the note's `## Tokens` section. That mapping is hand-maintained, and a hand-maintained mapping is a drift surface, so prefer verbatim names.

**Do not label a block "verbatim" unless you have checked it.** That claim was made and was false on the founding artifact.

Only the **status and severity palette** is checked against the implementation, with `statuses.py` upstream: if the design disagrees, the design is wrong. Everything else is descriptive.

## Declare the viewport, or do not

`viewport: 900` in the note means the artifact **is** a surface and will be framed at that width. Omit it when the artifact is a *document about* a surface — a dossier of mocks — because framing a scrolling document at a device width demonstrates nothing.

This distinction is the artifact's, not the project's. Do not encode the platform (`mobile`, `desktop`): every design in a mobile repo would carry the same value, which is restatement.

## Revisions are commits

The rule is `../../instructions/TRACEABILITY.md`, "`[[design]]` links": one artifact per commit, with the reason in the message. Not six edits and one commit at the end, which is the loss the whole phase exists to prevent.

Two regenerated HTML files diff as a wall of noise, so the commit message and the note's `## Revisions` line are the only readable record of *why* anything changed.

## Checklist

- [ ] Single self-contained file; no external requests
- [ ] Every commentable part carries `data-design-region`, unique within the artifact
- [ ] Status/severity tokens use implementation names, or the note declares the mapping
- [ ] No "verbatim" claim that has not been checked
- [ ] `viewport:` declared if the artifact is a surface; omitted if it is a document
- [ ] The note's `## Regions` section names every region and what it is for
- [ ] Committed alone, with the reason in the message

## Starting points

Scaffolds by *section*, not by platform. A design opens with the problem, not the solution:

**A surface** (`viewport:` declared) — the states it must handle, including the empty and error cases, then the busy case. A surface designed only for the busy case usually looks broken, because quiet is the common state.

**A dossier** (no `viewport:`) — one plate per decision, each stating the problem before the proposal, with the alternatives that lost. Number plates stably; annotations reference them.

**A design system** (`role: system`) — use `docs/__templates__/design-system.md`. Same eight sections in every project so two projects are comparable by diff.
