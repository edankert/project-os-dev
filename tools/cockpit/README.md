# project-os-cockpit

Three-pane web cockpit for project-os documentation. The centre pane renders any `.md` note as a linked HTML page at request time — no build step — with frontmatter-aware metadata, `[[wikilink]]` resolution, project-os ID linking, and live reload via SSE. The left and right panes surface features-by-phase navigation, backlinks, and outbound links.

## What it gives you

- Browse any project-os repo's `docs/` tree as HTML in a browser, on-demand. Edit a note in your editor and the page in your browser soft-reloads within a fraction of a second.
- `[[FEAT-0008]]` and `[[Target|Display]]` style links resolve correctly across the whole `docs/` tree, including the project-os ID conventions (`TASK-####`, `FEAT-####`, `REQ-####`, etc.).
- Standard Markdown images (`![Alt](./image.png)`) and Obsidian image embeds (`![[image.png]]`, `![[image.png|320]]`) render from local image assets under `docs/`, including nearby `__attachments__/` folders and unique image filenames elsewhere in the docs tree.
- YAML frontmatter renders as a metadata strip per page (status, owner, parent, links).
- Auto-generated index pages by status, parent, or type, including rare/project-supporting types such as decisions, tests, workflows, plans, and references.
- Backlinks panel showing which other notes link to the page you're viewing.
- Project mode surfaces a recursive untyped `docs/` tree, a typed `References` section, and selected top-level human-facing docs.
- Optional embedded local-only terminal panel for running an AI coding assistant (Claude Code / Codex) alongside the docs while editing in real time.

## Stack

- Python 3.11+
- `markdown` + selected `pymdownx` extensions for the renderer
- `python-frontmatter` for YAML frontmatter
- `watchdog` for file-change events
- Stdlib `http.server` for HTTP and a small SSE handler for Server-Sent Events
- Optional: [`ttyd`](https://github.com/tsl0922/ttyd) wrapping `claude` (or `codex`) for the terminal panel

No Node.js, no build step, no static-site generator.

## Run

```bash
# from a project-os repo root
tools/cockpit/run.sh docs --bind 127.0.0.1 --port 8765

# or, after installing this package directly
project-os-cockpit /path/to/your/project-os/repo/docs --bind 127.0.0.1 --port 8765
```

## Project-os layout

This repo is itself a project-os repo. See:

- `SNAPSHOT.yaml` — current state (focus, item statuses, counters)
- `docs/` — structured lifecycle records plus project reference/research documentation
- `tools/instructions/`, `tools/skills/` — the project-os system rules
- `tools/cockpit/run.sh` — the local wrapper for this browser tool

To consume this tool from another project-os repo, sync template-owned files with `tools/scripts/sync-project-os.sh <path-to-upstream-project-os>` or copy `tools/cockpit/` with the rest of `tools/`.

## Project Mode Docs

The cockpit indexes Markdown from `docs/`. This includes structured lifecycle records plus non-lifecycle project documentation under areas such as `docs/reference/` or `docs/research/`.

Project mode separates raw filesystem browsing from typed reference records:

- `Docs tree` lists untyped Markdown under `docs/`, preserving the directory structure so generated pages and deeply nested project documentation remain browsable without promoting them into lifecycle/type views. Lifecycle-record directories such as `changes/`, `features/`, `issues/`, `requirements/`, `tests/`, and `workflows/` are excluded from this tree because they already have dedicated cockpit views.
- `References` lists notes explicitly typed as `type: [[reference]]` or `type: reference`. It is a curated semantic section, not a second directory browser.

The only Markdown files outside `docs/` surfaced by default are selected top-level human-facing docs: `README.md`, `ROADMAP.md`, and `SECURITY.md`. Operator/LLM materials such as `AGENTS.md`, `CONTEXT.md`, `LLM_BRIEF.md`, and `tools/**` remain outside the default stakeholder cockpit.

## Images

Images should live under `docs/` so the cockpit can serve them safely through `/docs/...`. Both standard Markdown and Obsidian image syntax are supported:

```md
![System topology](./__attachments__/topology.svg)
![[topology.svg]]
![[chart.png|640]]
```

Resolution prefers explicit relative paths from the current note, then common sibling attachment directories such as `__attachments__/`, `attachments/`, `assets/`, and `images/`, then unique or nearest matching image filenames anywhere under `docs/`. Supported image extensions are `.svg`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, and `.avif`.

## License

MIT. See `LICENSE`.
