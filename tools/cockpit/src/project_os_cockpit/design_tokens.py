"""Scoped palette parity: a design's status colours against the implementation.

`base.css` and `cockpit.css` both restated the status palette, drifted, and the
corpus rendered a wrong colour for weeks — ISS-0023, which produced TST-0019's
parity suite and `statuses.py` as the single source. A design artifact that
declares status colours is the *same failure on a new surface*, and it is
checkable by the same means.

**Scope is the status and severity palette only.** Not spacing, not type scale,
not the artifact's own chrome. That narrowing is the whole point: an earlier
draft claimed the parity check justified building the design bench at all, and
independent review refuted it — the founding artifact names its tokens
``--m-done`` / ``--t-feature`` against an implementation saying ``--status-done``
/ ``--severity-critical``, so a general token comparison needs a name mapping,
and a hand-maintained mapping is the drift surface one level up.

**Direction of authority: the implementation is upstream.** If a design and
`base.css` disagree about a status colour, the *design* is wrong. That is
stated because a parity check with no declared direction accumulates waivers
instead of fixes — and because the two sides genuinely disagreed about the
arrow on the day this was written (a task note said the design was upstream
while DES-0001's own Maintenance section said to update the design when the
surfaces change).

A design that declares no status tokens is **silent, not failing**. Most
designs specify a surface, not a palette; demanding tokens from all of them
would make the check noise.
"""

from __future__ import annotations

import re
from pathlib import Path

#: Token families in scope. Anything else in an artifact is its own business.
SCOPED_PREFIXES: tuple[str, ...] = ("--status-", "--severity-")

_DECL_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)[;}]")


def read_tokens(text: str, prefixes: tuple[str, ...] = SCOPED_PREFIXES) -> dict[str, str]:
    """In-scope custom properties -> normalised value, **first declaration wins**.

    First-wins is not arbitrary. A stylesheet declares each token once per
    scheme — ``--status-done`` appears in `:root` and again in the dark block —
    and taking the last would compare a design's light palette against the
    implementation's dark one. That exact bug shipped in the family-palette
    check earlier today and reported a divergence that did not exist; anyone
    following it would have "fixed" three apps to the wrong value.
    """
    out: dict[str, str] = {}
    for name, value in _DECL_RE.findall(text):
        if not name.startswith(prefixes):
            continue
        out.setdefault(name, normalise(value))
    return out


def normalise(value: str) -> str:
    """Collapse whitespace so ``hsl(212 48% 42%)`` compares equal however it
    was spaced. Deliberately does *not* convert between colour spaces: a design
    written in hex and an implementation written in hsl are a real difference
    worth reporting, because one of them was retyped from the other."""
    return re.sub(r"\s+", " ", value.strip()).rstrip(";").strip()


def compare(design_css: str, impl_css: str) -> dict[str, list]:
    """Compare a design's scoped palette against the implementation's.

    Returns ``agree`` / ``diverged`` / ``unknown``. ``unknown`` is a token the
    design declares that the implementation does not have — usually a design
    inventing a status, which is a finding rather than an error, since a design
    proposing a *new* status is a legitimate thing for a design to do.
    """
    want = read_tokens(impl_css)
    got = read_tokens(design_css)
    agree, diverged, unknown = [], [], []
    for token, value in sorted(got.items()):
        if token not in want:
            unknown.append({"token": token, "design": value})
        elif want[token] != value:
            diverged.append({"token": token, "design": value,
                             "implementation": want[token]})
        else:
            agree.append(token)
    return {"agree": agree, "diverged": diverged, "unknown": unknown}


def check_design_assets(docs_root: Path, static_root: Path) -> dict[str, dict]:
    """Every design artifact that declares scoped tokens, against the impl.

    Silent for designs that declare none — most designs specify a surface, not
    a palette, and demanding tokens from all of them would make this noise.
    """
    impl = ""
    for name in ("base.css", "cockpit.css"):
        p = static_root / name
        if p.is_file():
            impl += p.read_text(encoding="utf-8")

    results: dict[str, dict] = {}
    designs_dir = docs_root / "designs"
    if not designs_dir.is_dir():
        return results
    for artifact in sorted(designs_dir.rglob("*.html")):
        text = artifact.read_text(encoding="utf-8", errors="replace")
        if not read_tokens(text):
            continue
        results[artifact.relative_to(docs_root).as_posix()] = compare(text, impl)
    return results
