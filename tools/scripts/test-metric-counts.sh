#!/usr/bin/env bash
# compute_metric_counts on made-up notes (project-os-dev ISS-0020, ISS-0021,
# ISS-0035): the field counts, and that a status comes from the file that
# claims the id, whether or not the index already parsed it.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$HERE/validate-docs.py" <<'PYEOF'
import importlib.util, sys, tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
failures = n = 0
def check(desc, ok):
    global failures, n
    n += 1; failures += not ok
    print("  %s %s" % ("ok  " if ok else "FAIL", desc))
tmp = Path(tempfile.mkdtemp())
def note(name, **fm):
    p = tmp / (name + ".md")
    p.write_text("---\n" + "".join("%s: %s\n" % kv for kv in fm.items()) + "---\n", encoding="utf-8")
    return p
idx, cl = {}, {}
def add(nid, name, **fm):
    p = note(name, id=nid, **fm); idx[nid] = (p, dict(fm, id=nid)); cl[nid] = [p]
add("TST-0001", "TST-0001-A", status="passing", command="make test")
add("TST-0002", "TST-0002-B", status="passing")
add("TST-0003", "TST-0003-C", status="active", level="acceptance", command="make walk")
add("TASK-0001", "TASK-0001-D", status="done", verification_waiver="a reason")
add("TASK-0002", "TASK-0002-E", status="done")
items = {"tasks": {"TASK-0002": {"status": "done", "verification_waiver": "in the snapshot"},
                   "TASK-0001": {"status": "done", "verification_waiver": "both places"}}}
c = vd.compute_metric_counts(items, idx, cl)
check("a test with a command: is executable", c["tests_executable"] == 1)
check("a test without one is manual", c["tests_manual"] == 1)
check("an acceptance check is in neither count", c["tests_executable"] + c["tests_manual"] == c["tests_total"] == 2)
check("a waiver in a note or a snapshot entry is counted once per item", c["waivers_outstanding"] == 2)
# ISS-0035: the index holds an impostor whose filename merely contains the id
real = note("FEAT-0009-Real", id="FEAT-0009", status="done")
impostor = note("CHG-20260525-FEAT-0009-Polish", status="merged")
c = vd.compute_metric_counts({}, {"FEAT-0009": (impostor, {"status": "merged"})}, {"FEAT-0009": [real]})
check("the claiming file's status counts, not the index's impostor", c["features_done"] == 1)
# the index's parse of the same file says done while the file now says draft:
# reading done proves the parse was reused rather than repeated
real.write_text("---\nid: FEAT-0009\nstatus: draft\n---\n", encoding="utf-8")
c = vd.compute_metric_counts({}, {"FEAT-0009": (real, {"status": "done", "id": "FEAT-0009"})}, {"FEAT-0009": [real]})
check("when the index parsed the claiming file, its parse is reused, not repeated", c["features_done"] == 1)
print("test-metric-counts: %d assertions, %d failure(s)" % (n, failures))
sys.exit(1 if failures else 0)
PYEOF
