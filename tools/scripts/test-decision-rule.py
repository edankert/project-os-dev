#!/usr/bin/env python3
"""TST-0004 (project-os-dev): DECISION-RULE holds its contract.

A decision note carrying a `## Rule` heading must carry a non-empty
`## Domain` and a non-empty `## Conformance`, at any status, and every
TST-#### named under Conformance must resolve — while check codes, type
names and prose there are never read as references (REQ-0025, ADR-0023).

Positive and negative cases both asserted: a check is only trusted to fire
where it claims to if it is also shown quiet where it claims to be. The two
template cases read the real docs/__templates__/adr.md, so template drift
that arms the check against its own output fails here rather than in the
first downstream repo to author an ADR. Two end-to-end cases run the full
validator (`main --repo-root`) over fixture repos, so unwiring the check —
deleting its one call site in validate() — fails the suite rather than
leaving it green while the corpus goes unchecked (independent-review
finding, 2026-08-12; the direct-call-only shape is shared by
test-retention.py and was invisible to every earlier assertion here).

Stdlib only. Exit 0 = all pass.

Usage: test-decision-rule.py [path-to-validator]
    The optional argument is an alternate validator module to hold to the
    same contract — e.g. tools/cockpit/src/project_os_cockpit/
    validate_docs_bundled.py — so the bundled copy is verifiable with one
    reproducible command instead of by relocating files into a scratch
    tree. Default: the validate-docs.py beside this script.
"""

from __future__ import annotations

import importlib.util as ilu
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "validate-docs.py"
_spec = ilu.spec_from_file_location("vd", TARGET)
vd = ilu.module_from_spec(_spec)
_spec.loader.exec_module(_spec and vd)

FAILURES = []
ASSERTIONS = [0]


def check(name, got, want):
    ASSERTIONS[0] += 1
    if got != want:
        FAILURES.append("%s: got %r, want %r" % (name, got, want))


def adr(name, body, status="proposed", the_id=None):
    """A decision-note file body: frontmatter + H1 + the given sections."""
    the_id = the_id or "ADR-" + name.split("-")[1]
    return (
        '---\ntype: "[[adr]]"\nid: %s\nstatus: %s\nowner: unassigned\n---\n\n'
        "# %s\n\n%s\n" % (the_id, status, the_id, body)
    )


def findings(notes, tests=(), items=None):
    """DECISION-RULE errors for a fixture repo holding `notes` in docs/decisions/."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dec = root / "docs" / "decisions"
        dec.mkdir(parents=True)
        for fname, body in notes.items():
            (dec / fname).write_text(body, encoding="utf-8")
        for tst_id in tests:
            tdir = root / "docs" / "tests"
            tdir.mkdir(parents=True, exist_ok=True)
            (tdir / ("%s-Fixture.md" % tst_id)).write_text(
                '---\ntype: "[[test]]"\nid: %s\nstatus: ready\n---\n\n# %s\n'
                % (tst_id, tst_id),
                encoding="utf-8",
            )
        note_index, _claimants = vd.build_note_index(root / "docs")
        report = vd.Report()
        vd.validate_decision_rule(root, items or {}, note_index, report)
        return [e for e in report.errors if "[DECISION-RULE]" in e]


RULE = "## Rule\nEvery fixture satisfies P.\n"
DOMAIN = "## Domain\nThe fixture registry, docs/decisions/.\n"
CONF_TST = "## Conformance\n[[TST-0001]] — the loop. Authority: the rule.\n"

# -- the cases that must fire ------------------------------------------------

got = findings({"ADR-0001-No-Domain.md": adr("ADR-0001", RULE + CONF_TST)}, tests=["TST-0001"])
check("absent Domain fires once", len(got), 1)
check("absent Domain names the section", "no `## Domain` section" in (got or [""])[0], True)

got = findings({"ADR-0001-Empty-Domain.md": adr("ADR-0001", RULE + "## Domain\n\n" + CONF_TST)}, tests=["TST-0001"])
check("empty Domain fires once", len(got), 1)
check("empty Domain says empty", "`## Domain` section is empty" in (got or [""])[0], True)

got = findings({"ADR-0001-No-Conformance.md": adr("ADR-0001", RULE + DOMAIN)})
check("absent Conformance fires once", len(got), 1)
check("absent Conformance names the section", "no `## Conformance` section" in (got or [""])[0], True)

got = findings({"ADR-0001-Empty-Conformance.md": adr("ADR-0001", RULE + DOMAIN + "## Conformance\n")})
check("empty Conformance fires once", len(got), 1)
check("empty Conformance says empty", "`## Conformance` section is empty" in (got or [""])[0], True)

got = findings({"ADR-0001-Dangling.md": adr(
    "ADR-0001", RULE + DOMAIN + "## Conformance\nTST-0042 — a loop. Authority: the rule.\n")})
check("dangling TST fires once", len(got), 1)
check("dangling TST is named", "TST-0042" in (got or [""])[0], True)

got = findings({"ADR-0001-Mixed.md": adr(
    "ADR-0001", RULE + DOMAIN
    + "## Conformance\n[[TST-0001]] and TST-0042 — loops. Authority: the rule.\n")},
    tests=["TST-0001"])
check("one dangling among resolving fires once", len(got), 1)
check("the dangling one is the one named", "TST-0042" in (got or [""])[0], True)

# Fires regardless of status: a proposed rule binds nothing yet but is
# malformed the same way (the cases above are `proposed`; this one is not).
got = findings({"ADR-0001-Accepted.md": adr("ADR-0001", RULE + CONF_TST, status="accepted")},
               tests=["TST-0001"])
check("accepted status does not exempt", len(got), 1)

# The accepted cost (ADR-0023, consequences): a casual `## Rule` used as prose
# scaffolding is checked as a rule-ADR and fails. Deliberate, so asserted.
got = findings({"ADR-0001-Casual.md": adr(
    "ADR-0001", "## Rule\nWe should generally be careful.\n\n## Decision\nBe careful.\n")})
check("casual Rule heading is checked as a rule-ADR", len(got), 2)

# -- the cases that must NOT fire ---------------------------------------------

got = findings({"ADR-0001-Clean.md": adr("ADR-0001", RULE + DOMAIN + CONF_TST, status="accepted")},
               tests=["TST-0001"])
check("fully-clean rule-ADR is silent", got, [])

got = findings({"ADR-0001-Snapshot-Resolved.md": adr(
    "ADR-0001", RULE + DOMAIN + "## Conformance\nTST-0007 — the loop. Authority: the rule.\n")},
    items={"tests": {"TST-0007": {"file": "docs/tests/TST-0007.md", "status": "ready"}}})
check("TST resolved via snapshot items is silent", got, [])

got = findings({"ADR-0001-Check-Code.md": adr(
    "ADR-0001", RULE + DOMAIN
    + "## Conformance\nThe `DECISION-RULE` and `REQ-BOXES` validator checks. "
    "On disagreement the validator is authoritative.\n")})
check("check-code-only Conformance is silent", got, [])

got = findings({"ADR-0001-Type.md": adr(
    "ADR-0001", RULE + DOMAIN
    + "## Conformance\nThe `Reading` sum type makes the violation unrepresentable. "
    "Authority: the type.\n")})
check("type-only Conformance is silent", got, [])

got = findings({"ADR-0001-Ordinary.md": adr(
    "ADR-0001", "## Context\nWhy.\n\n## Decision\nWhat.\n\n## Consequences\n- tradeoffs\n")})
check("ordinary ADR without Rule is silent", got, [])

got = findings({"ADR-0001-Quoted.md": adr(
    "ADR-0001",
    "## Context\nDiscusses the convention:\n\n```markdown\n## Rule\nQuoted, not stated.\n```\n\n"
    "## Decision\nNot a rule-ADR.\n")})
check("fenced Rule heading is quotation, not structure", got, [])

# The comment holds `## Rule` ALONE — were comments read as live structure,
# this note would be a rule-ADR missing both other sections and fire twice.
# That asymmetry is deliberate: it makes this case fail if comment-stripping
# regresses, where a fully-populated commented block would pass by accident.
got = findings({"ADR-0001-Commented.md": adr(
    "ADR-0001",
    "<!--\n## Rule\ndraft rule text, parked while the domain is enumerated\n-->\n\n"
    "## Context\nA draft rule parked in a comment.\n\n## Decision\nOrdinary.\n")})
check("commented Rule heading is not the marker", got, [])

# -- the shipped template, both ways ------------------------------------------

template = HERE.parent.parent / "docs" / "__templates__" / "adr.md"
if template.is_file():
    text = template.read_text(encoding="utf-8")
    got = findings({"ADR-0000-From-Template.md": text})
    check("the raw template trips nothing", got, [])
    uncommented = text.replace("<!--", "").replace("-->", "")
    got = findings({"ADR-0000-Block-Uncommented.md": uncommented})
    check("the template with the block uncommented validates clean", got, [])
else:
    print("note: docs/__templates__/adr.md not found beside this script; template cases skipped")

# -- end-to-end: the check is WIRED, not merely correct -----------------------
# Every case above calls validate_decision_rule directly, so none of them can
# see it go unwired: delete the one call site in validate() and they all stay
# green while the corpus goes unchecked (independent-review finding,
# 2026-08-12). These two run the real entry point over fixture repos. The
# clean twin is what makes the malformed twin's exit 1 attributable to
# DECISION-RULE rather than to fixture noise.


def _run_full_validator(rule_body):
    """(exit code, output) of the real CLI — `python3 TARGET --repo-root` — over a one-ADR fixture repo.

    A subprocess, not an in-process `vd.main(...)` call, for two reasons: it is
    the genuine article (the exact invocation hooks and CI make), and an
    imported module's `__builtins__` is a dict, which the completeness walk in
    validate_status_tables correctly flags — a loading artifact the script
    form never has, since production always runs the validator as __main__.
    """
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dec = root / "docs" / "decisions"
        dec.mkdir(parents=True)
        (dec / "ADR-0001-Wiring.md").write_text(adr("ADR-0001", rule_body), encoding="utf-8")
        (root / "SNAPSHOT.yaml").write_text(
            'version: 1\nupdated: "2026-08-12T00:00Z"\ncounters:\n  ADR: 1\n'
            'focus:\n  task: ""\nitems:\n  decisions: {}\n',
            encoding="utf-8",
        )
        proc = subprocess.run(
            [sys.executable, str(TARGET), "--repo-root", str(root)],
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode, proc.stdout + proc.stderr


code, out = _run_full_validator(RULE)  # `## Rule` alone: malformed twice over
check("end-to-end: a malformed rule-ADR fails the full validator", code, 1)
check("end-to-end: the finding is DECISION-RULE", "[DECISION-RULE]" in out, True)
code, _out = _run_full_validator(RULE + DOMAIN
                                 + "## Conformance\nThe type makes it unrepresentable. Authority: the type.\n")
check("end-to-end: the clean twin passes the full validator", code, 0)


def main():
    print("test-decision-rule: %d assertions, %d failure(s)" % (ASSERTIONS[0], len(FAILURES)))
    for f in FAILURES:
        print("  FAIL " + f)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
