"""Wikilink parsing + resolution.

Two consumers:

1. The Markdown body — handled by ``WikilinkExtension`` registering an
   ``InlineProcessor`` so wikilinks inside fenced code blocks are left
   alone (the markdown parser already strips them out before inline
   patterns run).
2. The metadata strip — handled by :func:`resolve_text_to_html`, which
   resolves wikilinks inside plain-text frontmatter values (e.g.
   ``related: ["[[FEAT-0001]]"]``) without touching the rest of the
   markdown pipeline.

Both paths share a single regex and a single resolver Protocol so the two
consumers stay consistent.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree
from html import escape
from typing import Callable, Optional

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor

# Captures: group(1) = target, group(2) = optional display text.
WIKILINK_RE: re.Pattern[str] = re.compile(r"\[\[([^|\]\n]+)(?:\|([^\]\n]+))?\]\]")
IMAGE_EMBED_RE: re.Pattern[str] = re.compile(r"!\[\[([^|\]\n]+)(?:\|([^\]\n]+))?\]\]")

Resolver = Callable[[str], Optional[str]]
ImageResolver = Callable[[str], Optional[str]]


def resolve_text_to_html(text: str, resolver: Resolver) -> str:
    """Resolve wikilinks inside a plain-text string to HTML.

    Non-wikilink text is HTML-escaped. Resolved targets become anchors;
    unresolvable ones become ``<span class="broken-wikilink">[[X]]</span>``.
    """
    if not text:
        return ""
    out: list[str] = []
    pos = 0
    for m in WIKILINK_RE.finditer(text):
        out.append(escape(text[pos : m.start()]))
        out.append(_render_match(m, resolver))
        pos = m.end()
    out.append(escape(text[pos:]))
    return "".join(out)


def _render_match(m: re.Match[str], resolver: Resolver) -> str:
    target = m.group(1).strip()
    display = (m.group(2) or target).strip()
    url = resolver(target)
    if url:
        return f'<a href="{escape(url)}">{escape(display)}</a>'
    return f'<span class="broken-wikilink" title="unresolved wikilink">{escape(m.group(0))}</span>'


class _WikilinkInlineProcessor(InlineProcessor):
    """Markdown InlineProcessor wrapping the resolver."""

    def __init__(self, pattern: str, resolver: Resolver) -> None:
        super().__init__(pattern)
        self._resolver = resolver

    def handleMatch(  # type: ignore[override]
        self, m: re.Match[str], data: str
    ) -> tuple[etree.Element, int, int]:
        target = m.group(1).strip()
        display = (m.group(2) or target).strip()
        url = self._resolver(target)
        if url:
            el = etree.Element("a")
            el.set("href", url)
            el.text = display
        else:
            el = etree.Element("span")
            el.set("class", "broken-wikilink")
            el.set("title", "unresolved wikilink")
            el.text = m.group(0)
        return el, m.start(0), m.end(0)


class _ImageEmbedInlineProcessor(InlineProcessor):
    """Obsidian ``![[image.png]]`` embed support."""

    def __init__(self, pattern: str, resolver: ImageResolver) -> None:
        super().__init__(pattern)
        self._resolver = resolver

    def handleMatch(  # type: ignore[override]
        self, m: re.Match[str], data: str
    ) -> tuple[etree.Element, int, int]:
        target = m.group(1).strip()
        modifier = (m.group(2) or "").strip()
        url = self._resolver(target)
        if url:
            el = etree.Element("img")
            el.set("src", url)
            alt, width, height = _parse_image_modifier(modifier)
            el.set("alt", alt or target)
            el.set("class", "obsidian-image-embed")
            if width:
                el.set("width", width)
            if height:
                el.set("height", height)
        else:
            el = etree.Element("span")
            el.set("class", "broken-wikilink")
            el.set("title", "unresolved image embed")
            el.text = m.group(0)
        return el, m.start(0), m.end(0)


class WikilinkExtension(Extension):
    """Registers the wikilink inline pattern with python-markdown."""

    def __init__(
        self,
        resolver: Resolver,
        *,
        image_resolver: ImageResolver | None = None,
    ) -> None:
        super().__init__()
        self._resolver = resolver
        self._image_resolver = image_resolver

    def extendMarkdown(self, md) -> None:  # type: ignore[override]
        if self._image_resolver is not None:
            md.inlinePatterns.register(
                _ImageEmbedInlineProcessor(IMAGE_EMBED_RE.pattern, self._image_resolver),
                "obsidian_image_embed",
                180,
            )
        # Priority 175 is above the standard ``link`` (160) and ``reference``
        # (170) inline patterns — wikilinks are matched first so the trailing
        # ``]]`` can't be misread as the close of a reference link.
        md.inlinePatterns.register(
            _WikilinkInlineProcessor(WIKILINK_RE.pattern, self._resolver),
            "wikilink",
            175,
        )


def _parse_image_modifier(modifier: str) -> tuple[str | None, str | None, str | None]:
    if not modifier:
        return None, None, None
    if re.fullmatch(r"\d+", modifier):
        return None, modifier, None
    size = re.fullmatch(r"(\d+)x(\d+)", modifier)
    if size:
        return None, size.group(1), size.group(2)
    return modifier, None, None
