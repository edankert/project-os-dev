"""Obsidian callouts, rendered (FEAT-0095 / TASK-0397).

    > [!note] Accepted — 2026-08-12 (user:edwin)
    > Option 3, but consequence 3 needs the digest question settled first.

Obsidian renders that as a titled, coloured block. The cockpit rendered it as
a plain blockquote with the literal `[!note]` still in the text — measured
2026-08-12, which is what made it worth building before anything started
writing them.

**One syntax, two readers.** The decision record ADR-0025 asks for is prose
appended to a note, and prose in the record has to survive being read in
Obsidian as well as here. Inventing a cockpit-only marker would have made the
tool the only place the record is legible, which is the failure every
convention in this project is written to avoid.

Unknown types degrade to a plain blockquote **with their title kept**, rather
than to the literal marker: Obsidian ships a couple of dozen callout types and
a downstream repo may use any of them, so an unrecognised one is a rendering
question, never an error.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

#: `> [!type]` optionally `+`/`-` (Obsidian's fold markers) and a title.
CALLOUT_RE = re.compile(
    r"^>\s*\[!(?P<type>[A-Za-z-]+)\](?P<fold>[+-]?)\s*(?P<title>.*)$"
)

#: The types that get their own colour. Everything else renders as a callout
#: with its type as a data attribute and the default palette — visible, and
#: never a literal `[!whatever]` in the reader's face.
KNOWN_TYPES: frozenset[str] = frozenset({
    "note", "info", "tip", "hint", "important",
    "question", "help", "faq",
    "warning", "caution", "attention",
    "danger", "error", "bug",
    "success", "check", "done",
    "example", "quote", "cite", "abstract", "summary", "tldr",
    "todo", "failure", "fail", "missing",
})


class _CalloutProcessor(BlockProcessor):
    """One blockquote whose first line is `> [!type] title`."""

    def test(self, parent: etree.Element, block: str) -> bool:  # noqa: D102
        first = block.split("\n", 1)[0]
        return bool(CALLOUT_RE.match(first))

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:  # noqa: D102
        block = blocks.pop(0)
        lines = block.split("\n")
        m = CALLOUT_RE.match(lines[0])
        if m is None:                                # pragma: no cover — test() gates
            blocks.insert(0, block)
            return False
        kind = m.group("type").lower()
        title = m.group("title").strip()

        wrapper = etree.SubElement(parent, "div")
        wrapper.set("class", "callout")
        wrapper.set("data-callout", kind)
        if kind not in KNOWN_TYPES:
            # Said in the markup rather than silently: a stylesheet can choose
            # to mark it, and a test can find it.
            wrapper.set("data-callout-unknown", "true")

        head = etree.SubElement(wrapper, "div")
        head.set("class", "callout-title")
        # An untitled callout takes its type as the title, which is Obsidian's
        # own behaviour and reads better than an empty bar.
        head.text = title or kind.capitalize()

        body_lines = [
            re.sub(r"^>\s?", "", line) for line in lines[1:]
        ]
        body_text = "\n".join(body_lines).strip()
        if body_text:
            body = etree.SubElement(wrapper, "div")
            body.set("class", "callout-body")
            # Parsed as markdown, so a link or emphasis inside a callout is a
            # link or emphasis. `parseBlocks` is what makes it a block context
            # rather than a run of inline text.
            self.parser.parseBlocks(body, body_text.split("\n\n"))
        return True


class CalloutExtension(Extension):
    """Registers the callout block processor."""

    def extendMarkdown(self, md) -> None:  # noqa: N802, D102 — python-markdown API
        # Ahead of `blockquote`, or the blockquote processor claims the block
        # first and the callout never runs.
        md.parser.blockprocessors.register(
            _CalloutProcessor(md.parser), "callout", 21.5,
        )
