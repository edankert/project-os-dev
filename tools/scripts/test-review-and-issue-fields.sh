#!/usr/bin/env bash
# REVIEW-ROUND, ISSUE-REPORTER and ISSUE-QUESTION on made-up notes
# (project-os-dev TASK-0129, TASK-0133). Each case names the note and the code it
# must, or must not, draw.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$HERE/validate-docs.py" <<'PYEOF'
import importlib.util, sys, tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
tmp = Path(tempfile.mkdtemp())
def note(nid, fm, body=""):
    p = tmp / (nid + ".md"); p.write_text("---\n---\n" + body, encoding="utf-8"); return nid, (p, fm)
NEW, OLD = "2026-09-20", "2026-09-01"
iss = lambda **k: dict({"type": "[[issue]]", "status": "open", "created": NEW, "owner": "user:edwin"}, **k)
cases = [
    # (description, note, code, expected to fire)
    ("round 3 is refused", note("FEAT-0001", {"type": "[[feature]]", "review_round": 3, "review_date": "2026-09-20"}), "REVIEW-ROUND", True),
    ("round 2 is fine", note("FEAT-0002", {"type": "[[feature]]", "review_round": 2, "review_date": "2026-09-20"}), "REVIEW-ROUND", False),
    ("round 8 from before the cap is history, not a violation", note("TST-0002", {"type": "[[test]]", "review_round": 8, "review_date": "2026-08-10"}), "REVIEW-ROUND", False),
    ("no round is fine", note("TST-0001", {"type": "[[test]]"}), "REVIEW-ROUND", False),
    ("a new open issue with no reporter", note("ISS-0001", iss()), "ISSUE-REPORTER", True),
    ("a reporter outside the vocabulary", note("ISS-0002", iss(reported_by="someone")), "ISSUE-REPORTER", True),
    ("reported_by: review is fine", note("ISS-0003", iss(reported_by="review")), "ISSUE-REPORTER", False),
    ("reported_by: user:edwin is fine", note("ISS-0004", iss(reported_by="user:edwin")), "ISSUE-REPORTER", False),
    ("an issue from before the cutover is not checked", note("ISS-0005", iss(created=OLD)), "ISSUE-REPORTER", False),
    ("a fixed issue is not checked", note("ISS-0006", iss(status="fixed")), "ISSUE-REPORTER", False),
    ("waits on Edwin with no question", note("ISS-0007", iss(reported_by="agent"), "Whether to ship it is Edwin's call."), "ISSUE-QUESTION", True),
    ("waits on the owner with no question", note("ISS-0008", iss(reported_by="agent"), "This waits on the owner."), "ISSUE-QUESTION", True),
    ("waits on Edwin with a question", note("ISS-0009", iss(reported_by="agent", question="Ship X or Y? Recommend X."), "Edwin's call."), "ISSUE-QUESTION", False),
    ("no mention of the owner", note("ISS-0010", iss(reported_by="agent"), "The page freezes on load."), "ISSUE-QUESTION", False),
    ("an old issue waiting on Edwin is not checked", note("ISS-0011", iss(created=OLD), "Edwin's call."), "ISSUE-QUESTION", False),
    ("a new issue at triage with no reporter", note("ISS-0012", iss(status="triage")), "ISSUE-REPORTER", True),
    ("working for Edwin is not waiting on him", note("ISS-0013", iss(reported_by="agent"), "Found while working for Edwin on the release."), "ISSUE-QUESTION", False),
]
# The real issue template: its comment on `question:` says "only when it waits
# on the owner", which must not count (FEAT-0037's review found it did).
tpl = (Path(sys.argv[1]).parents[2] / "docs/__templates__/issue.md").read_text(encoding="utf-8")
tp = tmp / "ISS-0014.md"; tp.write_text(tpl, encoding="utf-8")
cases.append(("a new issue made from the template draws no ISSUE-QUESTION", ("ISS-0014", (tp, iss(reported_by="agent"))), "ISSUE-QUESTION", False))
failures = 0
for desc, (nid, entry), code, expect in cases:
    r = vd.Report()
    vd.validate_review_and_issue_fields({nid: entry}, {}, r)
    fired = any("[%s] %s " % (code, nid) in m for m in r.errors + r.warnings)
    ok = fired == expect
    failures += not ok
    print("  %s %s" % ("ok  " if ok else "FAIL", desc))
r = vd.Report(); vd.validate_review_and_issue_fields(dict([cases[0][1]]), {}, r)
ok = any("REVIEW-ROUND" in m for m in r.errors); failures += not ok
print("  %s REVIEW-ROUND is an error, not a warning" % ("ok  " if ok else "FAIL"))
print("test-review-and-issue-fields: %d unit assertions, %d failure(s)" % (len(cases) + 1, failures))
sys.exit(1 if failures else 0)
PYEOF
unit=$?
# End to end: the validator's own run reaches the checks, not only the function.
REPO="$(cd "$HERE/../.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cp -R "$REPO/SNAPSHOT.yaml" "$REPO/docs" "$T/"; mkdir -p "$T/tools"; cp -R "$REPO/tools/scripts" "$REPO/tools/instructions" "$T/tools/"
mkdir -p "$T/docs/issues"
printf -- '---\ntype: "[[issue]]"\nid: ISS-0901\ntitle: "x"\nstatus: triage\nowner: user:edwin\ncreated: 2026-09-20\nupdated: 2026-09-20\n---\n\n# x\n\nWhether to ship it is Edwin'"'"'s call.\n' > "$T/docs/issues/ISS-0901-x.md"
out="$(PYTHONDONTWRITEBYTECODE=1 python3 "$T/tools/scripts/validate-docs.py" --repo-root "$T" 2>&1)"
e2e=0
for code in ISSUE-REPORTER ISSUE-QUESTION; do
  if grep -q "\[$code\] ISS-0901 " <<<"$out"; then echo "  ok   the validator's run reports $code"; else echo "  FAIL the validator's run reports $code"; e2e=$((e2e + 1)); fi
done
echo "test-review-and-issue-fields: end to end, $e2e failure(s)"
[ "$unit" -eq 0 ] && [ "$e2e" -eq 0 ]
