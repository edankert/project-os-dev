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

from . import templates
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
    extensions: list[Any] = list(MARKDOWN_EXTENSIONS_BASE)
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
    return md.convert(text)


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
