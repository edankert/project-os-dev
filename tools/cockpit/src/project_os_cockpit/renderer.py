"""Markdown -> HTML render pipeline.

Reads a ``.md`` source file, splits frontmatter via ``python-frontmatter``,
runs Markdown via ``markdown`` + selected ``pymdownx`` extensions and the
project's own :class:`project_os_cockpit.wikilinks.WikilinkExtension`, and wraps
the result in the shared HTML shell from :mod:`project_os_cockpit.templates`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import frontmatter
import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

import html as _html
import itertools as _it
import logging
import re as _re

from . import templates
from .note_writes import _criterion_text
from .callouts import CalloutExtension
from .wikilinks import Resolver, WikilinkExtension


AssetResolver = Callable[[str, Path], str | None]


MARKDOWN_EXTENSIONS_BASE: list[str] = [
    "tables",
    "fenced_code",
    "toc",
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.tasklist",
]

MARKDOWN_EXTENSION_CONFIGS: dict[str, dict[str, Any]] = {
    "toc": {"permalink": False},
    "pymdownx.highlight": {
        "use_pygments": True,
        "noclasses": False,
        "css_class": "codehilite",
    },
    "pymdownx.tasklist": {
        # Obsidian-style: render `- [x]` / `- [ ]` as visual checkboxes,
        # read-only (we're a renderer, not an editor — the source is the
        # truth, the page is the view).
        "clickable_checkbox": False,
        "custom_checkbox": True,
    },
}


def render_markdown_body(
    source_path: Path,
    *,
    resolver: Resolver | None = None,
    asset_resolver: AssetResolver | None = None,
) -> str:
    """Render just the body of a ``.md`` file to HTML, no page chrome.

    Used by the landing-page fallback to embed a README inside the cockpit
    shell without re-running the full ``page()`` wrapper.
    """
    raw = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    return _markdown_to_html(
        post.content,
        resolver=resolver,
        asset_resolver=asset_resolver,
        source_path=source_path,
    )


def render_markdown_text(
    body: str,
    *,
    source_path: Path,
    resolver: Resolver | None = None,
    asset_resolver: AssetResolver | None = None,
) -> str:
    """Render a markdown *fragment* already in memory (ISS-0151).

    `render_markdown_body` reads a file; the brief's sections are slices of one
    that has already been parsed, and re-reading to re-split it would put the
    section boundaries in two places.
    """
    return _markdown_to_html(
        body,
        resolver=resolver,
        asset_resolver=asset_resolver,
        source_path=source_path,
    )


def render_markdown_file(
    source_path: Path,
    *,
    rel_path: str,
    resolver: Resolver | None = None,
    asset_resolver: AssetResolver | None = None,
    url_prefix: str = "/docs",
    reload_source: str | None = None,
) -> str:
    """Render a single ``.md`` file to a complete HTML document.

    ``rel_path`` is the route-root-relative path used for the breadcrumb;
    the actual filesystem read uses ``source_path``. ``url_prefix`` is the URL
    root for that route, defaulting to ``/docs``. ``resolver`` (when
    provided) is consulted by :class:`WikilinkExtension` and by the
    metadata-strip wikilink resolver in :mod:`project_os_cockpit.templates`.
    """
    raw = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    metadata: dict[str, Any] = dict(post.metadata or {})
    body_md = post.content

    title = _derive_title(metadata, body_md, source_path)
    body_html = _markdown_to_html(
        body_md,
        resolver=resolver,
        asset_resolver=asset_resolver,
        source_path=source_path,
    )

    note_id = metadata.get("id") if isinstance(metadata.get("id"), str) else None
    route_prefix = url_prefix.rstrip("/")
    url = f"{route_prefix}/{rel_path}" if route_prefix else f"/{rel_path}"
    cockpit_active = {
        "id": note_id,
        "path": rel_path,
        "url": url,
        "title": title,
    }

    return templates.page(
        title=title,
        body_html=body_html,
        rel_path=rel_path,
        metadata=metadata,
        resolver=resolver,
        reload_source=rel_path if reload_source is None else reload_source,
        path_prefix=route_prefix or "",
        cockpit_active=cockpit_active,
    )


def _markdown_to_html(
    text: str,
    *,
    resolver: Resolver | None,
    asset_resolver: AssetResolver | None,
    source_path: Path,
) -> str:
    # Callouts before the wikilink extension for no ordering reason — they
    # are independent — but registered ALWAYS, including for notes rendered
    # without a resolver, because a decision record is prose in a file and
    # is read from more places than the note page (FEAT-0095).
    # **No acceptance-mark extension** (ISS-0192). It stamped every row of a
    # rendered suite with its address so the client could draw a control, and
    # it lost its subject when the last file-shaped suite migrated: no repo
    # stores an acceptance suite as a document any more (ADR-0030).
    #
    # Deleting it also fixes what it had become. `ACCEPTANCE_TESTS_v2.1.0.md`
    # in `../your-trainer` is a FROZEN record of what v2.1.0 was measured
    # against, and it still parses as 300 checks — so it went on rendering 300
    # live mark controls, writing to a file that no longer exists. Before the
    # migration those clicks SUCCEEDED, against the living suite: a mark
    # clicked on a frozen record written into a different document, matched by
    # section-and-ordinal in a file sharing none of its check titles.
    #
    # A rule about which documents may be clicked would have been the other
    # fix. This one removes the question.
    extensions: list[Any] = [*MARKDOWN_EXTENSIONS_BASE, CalloutExtension()]
    if resolver is not None:
        image_resolver = (
            (lambda target: asset_resolver(target, source_path))
            if asset_resolver is not None
            else None
        )
        extensions.append(WikilinkExtension(resolver, image_resolver=image_resolver))
    if asset_resolver is not None:
        extensions.append(ImageSourceExtension(asset_resolver, source_path))
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
        output_format="html5",
        tab_length=2,
    )
    return _annotate_checkbox_source(md.convert(text), text)


#: A rendered task-list checkbox, as pymdownx.tasklist emits it. Matched on
#: the input element rather than the `<li>`, because that is the node the
#: renderer already holds when a criterion is clicked.
log = logging.getLogger("project_os_cockpit.renderer")

_RENDERED_BOX_RE = _re.compile(r"<input(?=[^>]*\btype=\"checkbox\")")
def _annotate_checkbox_source(html: str, source_md: str) -> str:
    """Carry each checkbox's **raw** source prose onto its rendered input.

    ISS-0137. Markdown consumes inline markup on the way out: `` `x` ``
    becomes ``<code>x</code>``, ``[[y]]`` becomes an anchor, ``**z**``
    becomes ``<strong>``. A client that recovers the criterion by reading
    ``textContent`` therefore produces a string the *source* does not
    contain — and `note_writes.resolve_criterion` matches against the source
    line, exactly and deliberately, because ambiguity there is a refusal
    rather than a guess.

    The two never agreed for any criterion carrying markup, which measured
    on this corpus was **26 of 53 open criteria**. The tick prompt accepted
    the evidence and then the write was refused, which is the worst order to
    fail in: the reader has already done the thinking.

    So the raw line travels with the box. The correspondence is ordinal —
    the Nth rendered checkbox is the Nth task-list line in the source — the
    same walk `server._toggle_task_at` has always relied on for plain
    toggles, and the same document order Markdown guarantees.

    ``data-raw`` is the criterion's prose after ``_criterion_text``, so a
    ticked box carries the criterion rather than the criterion plus its
    evidence, and re-resolving addresses the criterion.
    """
    raws = [
        _criterion_text(line) for line in source_md.splitlines()
        if _criterion_text(line) is not None
    ]
    if not raws:
        return html

    # **The counts must agree, or nothing is labelled** (ISS-0175).
    #
    # The ordinal correspondence this function relies on is FALSE whenever
    # Markdown declines to make a list. A task list that opens immediately
    # after a paragraph line — no blank line between — is lazy continuation:
    # it is absorbed into the paragraph and renders **no checkboxes at all**,
    # while `_criterion_text` is line-based and counts every one.
    #
    # Measured on `your-trainer`'s acceptance suite: 579 source task lines,
    # 542 rendered inputs, and from the first divergence at box #257 every
    # subsequent box carried a DIFFERENT row's text — 285 of 542 mislabelled.
    #
    # `resolve_criterion` matches the source exactly and deliberately, because
    # ambiguity there is meant to be a refusal rather than a guess. Feeding it
    # a confidently wrong value defeats that. The over-count branch below
    # already states the principle — *"leaving the attribute off degrades to
    # the old behaviour rather than mislabelling a box with somebody else's
    # text"* — and this applies it to the whole document rather than to one
    # box, because a count mismatch means the alignment is unknowable, not
    # merely short.
    rendered_boxes = len(_RENDERED_BOX_RE.findall(html))
    if rendered_boxes != len(raws):
        log.warning(
            "checkbox annotation skipped: %d rendered boxes against %d source "
            "task lines. A task list that opens immediately after a paragraph "
            "renders no checkboxes; add a blank line before it.",
            rendered_boxes, len(raws),
        )
        return html

    # **No check address is emitted here, and none is emitted anywhere now.**
    # It used to live on the `<li>`, stamped by an acceptance treeprocessor
    # that ISS-0192 deleted along with the document surface it served. What
    # survives here is `data-raw` for the acceptance CRITERIA on feature and
    # requirement notes, which are a different population and still clickable.
    #
    # Kept as a warning to whoever considers putting an address back on a
    # rendered checkbox: emitting it in both places once produced 1088
    # addresses for 579 rows, which is how the double-stamping was caught.
    counter = _it.count()

    def _sub(match: "_re.Match[str]") -> str:
        idx = next(counter)
        if idx >= len(raws):
            # More rendered boxes than source lines should be impossible;
            # leaving the attribute off degrades to the old behaviour rather
            # than mislabelling a box with somebody else's text.
            return match.group(0)
        return f'{match.group(0)} data-raw="{_html.escape(raws[idx], quote=True)}"'

    return _RENDERED_BOX_RE.sub(_sub, html)


def _check_numbers(source_md: str) -> tuple[list[str], list[str]]:
    """Each task line's acceptance address, or ``""`` where it has none.

    Positional with `raws` above, and guarded by the same count agreement:
    this is only ever consulted when rendered boxes and source task lines
    already match, so the Nth entry belongs to the Nth box.

    A document that is not an acceptance suite yields all-empty and the
    attribute is simply not emitted.
    """
    from . import acceptance

    try:
        items = acceptance.parse(source_md)
    except Exception:                      # pragma: no cover — parse is total
        return [], []
    if not items:
        return [], []
    # `parse` walks task lines in document order and skips fences, exactly as
    # `_criterion_text` does, so the two lists correspond one-for-one. Asserted
    # by length rather than assumed: a mismatch means some other rule differs
    # between them, and the safe answer is to emit no addresses at all.
    numbers = [i.number for i in items]
    names = [i.name for i in items]
    raw_count = sum(
        1 for line in source_md.splitlines()
        if _criterion_text(line) is not None
    )
    return (numbers, names) if len(numbers) == raw_count else ([], [])


class ImageSourceTreeprocessor(Treeprocessor):
    """Resolve standard Markdown image URLs to stable ``/docs/...`` URLs."""

    def __init__(self, md, asset_resolver: AssetResolver, source_path: Path) -> None:
        super().__init__(md)
        self._asset_resolver = asset_resolver
        self._source_path = source_path

    def run(self, root):  # type: ignore[override]
        for el in root.iter("img"):
            src = el.get("src")
            if not src:
                continue
            resolved = self._asset_resolver(src, self._source_path)
            if resolved:
                el.set("src", resolved)
        return root


class ImageSourceExtension(Extension):
    def __init__(self, asset_resolver: AssetResolver, source_path: Path) -> None:
        super().__init__()
        self._asset_resolver = asset_resolver
        self._source_path = source_path

    def extendMarkdown(self, md) -> None:  # type: ignore[override]
        md.treeprocessors.register(
            ImageSourceTreeprocessor(md, self._asset_resolver, self._source_path),
            "project_os_image_sources",
            5,
        )


def _derive_title(metadata: dict[str, Any], body: str, source_path: Path) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return source_path.stem
