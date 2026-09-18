#!/usr/bin/env bash
# Every type's allowed statuses are read from STATUSES.md (project-os-dev
# ISS-0050): the template's file agrees with the built-in defaults, and a repo
# that edits a list there changes what the validator accepts.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$HERE/validate-docs.py" "$HERE/../.." <<'PYEOF'
import importlib.util, sys, tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
failures = n = 0
def check(desc, ok):
    global failures, n
    n += 1; failures += not ok
    print("  %s %s" % ("ok  " if ok else "FAIL", desc))
real = Path(sys.argv[2])
text = (real / "tools/instructions/STATUSES.md").read_text(encoding="utf-8")
check("STATUSES.md has a [[surface]] section", "## `[[surface]]`" in text)
# parse the template's file with the built-in default blanked, so only the file can supply it
saved = vd.ALLOWED_STATUS["surface"]; vd.ALLOWED_STATUS["surface"] = set()
parsed = vd.load_allowed_status(real)["surface"]
vd.ALLOWED_STATUS["surface"] = saved
check("the file's surface statuses equal the built-in default", parsed == set(saved))
root = Path(tempfile.mkdtemp()); (root / "tools/instructions").mkdir(parents=True)
(root / "tools/instructions/STATUSES.md").write_text(text.replace("## `[[surface]]`\n- Allowed: `active`, `retired`, `superseded`", "## `[[surface]]`\n- Allowed: `active`, `sunset`"), encoding="utf-8")
check("a repo's own list replaces the default", vd.load_allowed_status(root)["surface"] == {"active", "sunset"})
print("test-statuses-md: %d assertions, %d failure(s)" % (n, failures))
sys.exit(1 if failures else 0)
PYEOF
