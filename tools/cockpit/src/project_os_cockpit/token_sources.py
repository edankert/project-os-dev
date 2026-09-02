"""Synthesise CSS custom properties from native colour declarations.

Three fleet apps — `your-health` (Kotlin), `your-sudoku` and `your-trainer`
(Swift) — declare their palettes in source rather than CSS, so the living style
guide could not read them at all (ISS-0059).

**Synthesised at read time, never written to disk.** A generated file committed
beside the source is a second copy of the palette: edit `Color.kt`, forget to
regenerate, and the page shows stale values with total confidence. That is the
drift this whole feature exists to prevent, so nothing is generated ahead of
time — the sidecar parses the source on each request and the answer cannot be
older than the file.

**The source never leaves the machine.** Only extracted `--name: value` pairs
are emitted. That is why this is safer than serving the source file to the
frame, which the alternative design would have required.

**A colour that cannot be resolved is reported, not guessed.** Swift's
`Color.blue.opacity(0.3)` derives from a system colour whose value depends on
the platform and the appearance; there is no honest hex for it. Its name is
emitted with the source expression as the value, so the page shows the token
exists and says what it is instead of inventing a swatch.
"""

from __future__ import annotations

import re

#: `val Ident = Color(0xAARRGGBB)` / `0xRRGGBB`.
_KOTLIN = re.compile(
    r"\b(?:va[lr])\s+([A-Za-z_]\w*)\s*=\s*Color\(\s*0x([0-9A-Fa-f]{6,8})\s*\)")

#: `static let Ident = Color(red: 0x74 / 255.0, green: …, blue: …)`, and the
#: same with decimal components.
_SWIFT_RGB = re.compile(
    r"\b(?:static\s+)?let\s+([A-Za-z_]\w*)\s*=\s*Color\(\s*"
    r"red:\s*([0-9a-fA-Fx.]+)\s*/\s*255\.0\s*,\s*"
    r"green:\s*([0-9a-fA-Fx.]+)\s*/\s*255\.0\s*,\s*"
    r"blue:\s*([0-9a-fA-Fx.]+)\s*/\s*255\.0")

#: `let Ident = Color(red: 0.6, green: 0.6, blue: 0.6)` — SwiftUI's native
#: 0–1 doubles. The `/ 255.0` spelling above is one way of writing these, not
#: the only one (ISS-0073); reporting this form as unresolvable spends the
#: "no honest value" signal on a colour that has one.
_SWIFT_UNIT = re.compile(
    r"\b(?:static\s+)?let\s+([A-Za-z_]\w*)\s*=\s*Color\(\s*"
    r"red:\s*(\d*\.?\d+)\s*,\s*"
    r"green:\s*(\d*\.?\d+)\s*,\s*"
    r"blue:\s*(\d*\.?\d+)\s*\)")

#: Any other `let Ident = Color…` — named, but not resolvable to a value here.
_SWIFT_OTHER = re.compile(
    r"\b(?:static\s+)?let\s+([A-Za-z_]\w*)\s*=\s*(Color[^\n]*)")

#: `val Ident = Color.Something` — the Kotlin equivalent.
_KOTLIN_OTHER = re.compile(r"\b(?:va[lr])\s+([A-Za-z_]\w*)\s*=\s*(Color\.[^\n]*)")

_SUPPORTED = {".kt": "kotlin", ".swift": "swift"}


def supports(rel: str) -> bool:
    """True when this module can synthesise CSS for that path."""
    return any(rel.lower().endswith(ext) for ext in _SUPPORTED)


def _hex_from_argb(digits: str) -> tuple[str, str | None]:
    """(#rrggbb, alpha-or-None) from AARRGGBB or RRGGBB."""
    d = digits.upper()
    if len(d) == 8:
        alpha = int(d[:2], 16) / 255.0
        return "#" + d[2:], None if alpha >= 0.999 else "%.3g" % alpha
    return "#" + d, None


def _component(raw: str) -> int | None:
    try:
        return int(raw, 16) if raw.lower().startswith("0x") else int(float(raw))
    except (TypeError, ValueError):
        return None


def _safe(expr: str) -> str:
    """A source expression, reduced to something that cannot escape a CSS value.

    Only ever applied to text a `Color…` pattern already matched, and clipped —
    the point is to name what could not be resolved, not to relay source.
    """
    expr = re.split(r"\s+//", expr)[0]          # drop a trailing line comment
    cleaned = re.sub(r"[{};<>\"\\\n\r]", " ", expr).strip()
    return re.sub(r"\s+", " ", cleaned)[:80]


def synthesise_css(text: str, rel: str) -> str:
    """CSS custom properties for the colours declared in ``text``.

    Emitted inside ``:root`` because that is where the style guide looks for a
    palette — a token declared anywhere else has no page-level value.

    Token names are the **source identifiers, verbatim**. Converting
    ``PrimaryBlue`` to ``--primary-blue`` would read more like CSS and would
    stop anyone grepping the name they saw; the point of reading the
    implementation is that what you see is what is written.
    """
    lang = next((v for k, v in _SUPPORTED.items() if rel.lower().endswith(k)), None)
    if lang is None:
        return ""

    resolved: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []
    seen: set[str] = set()

    if lang == "kotlin":
        for name, digits in _KOTLIN.findall(text):
            if name in seen:
                continue
            seen.add(name)
            hexed, alpha = _hex_from_argb(digits)
            resolved.append((name, hexed if alpha is None
                             else "color-mix(in srgb, %s %s%%, transparent)"
                                  % (hexed, round(float(alpha) * 100))))
        for name, expr in _KOTLIN_OTHER.findall(text):
            if name not in seen:
                seen.add(name)
                unresolved.append((name, _safe(expr)))
    else:
        for name, r, g, b in _SWIFT_RGB.findall(text):
            comps = [_component(c) for c in (r, g, b)]
            if name in seen or any(c is None for c in comps):
                continue
            seen.add(name)
            resolved.append((name, "#%02X%02X%02X" % tuple(comps)))
        for name, r, g, b in _SWIFT_UNIT.findall(text):
            if name in seen:
                continue
            try:
                comps = [float(c) for c in (r, g, b)]
            except ValueError:
                continue
            if any(not 0.0 <= c <= 1.0 for c in comps):
                continue        # outside the unit interval — not this form
            seen.add(name)
            resolved.append(
                (name, "#%02X%02X%02X" % tuple(round(c * 255) for c in comps)))
        for name, expr in _SWIFT_OTHER.findall(text):
            if name not in seen:
                seen.add(name)
                unresolved.append((name, _safe(expr)))

    if not resolved and not unresolved:
        return "/* %s: no colour declarations recognised */\n" % _safe(rel)

    lines = ["/* synthesised from %s at read time — never written to disk */"
             % _safe(rel), ":root {"]
    for name, value in resolved:
        lines.append("  --%s: %s;" % (name, value))
    for name, expr in unresolved:
        # Named, with the source expression as its value: the page shows that
        # the token exists and what it derives from, rather than inventing a
        # swatch for a colour only the platform can resolve.
        lines.append("  --%s: %s;" % (name, expr))
    lines.append("}")
    return "\n".join(lines) + "\n"
