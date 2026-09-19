#!/usr/bin/env bash
# A SNAPSHOT.yaml that does not parse fails both the validator and
# sync-snapshot --check (project-os-dev ISS-0070). Before the fix, both fell
# back to the lenient subset parser on the syntax error and passed.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
failures=0; n=0
check() { n=$((n + 1)); if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi; }
python3 -c 'import yaml' 2>/dev/null || { echo "test-snapshot-parse: PyYAML not installed; skipped"; exit 0; }
cp -R "$REPO/SNAPSHOT.yaml" "$REPO/docs" "$T/"
mkdir -p "$T/tools"; cp -R "$REPO/tools/scripts" "$REPO/tools/instructions" "$T/tools/"
[ -d "$REPO/tools/sync" ] && cp -R "$REPO/tools/sync" "$T/tools/"
cd "$T" && git init -q && git config user.email t@t && git config user.name t && git add -A && git commit -qm base
vd() { python3 -B tools/scripts/validate-docs.py --repo-root "$T" 2>&1; }
check "the untouched copy has no SNAP-PARSE error" bash -c "! (python3 -B tools/scripts/validate-docs.py --repo-root '$T' 2>&1 | grep -q SNAP-PARSE)"
check "and passes sync-snapshot --check" python3 -B tools/scripts/sync-snapshot.py --repo-root "$T" --check --quiet
# An unterminated quoted string: PyYAML rejects it, the subset parser does not.
python3 - "$T/SNAPSHOT.yaml" <<'PY'
import sys; p = sys.argv[1]; s = open(p).read()
open(p, "w").write(s.replace("project:\n", 'project:\n  broken: "unterminated\n', 1))
PY
check "a snapshot that does not parse is a SNAP-PARSE error" bash -c "python3 -B tools/scripts/validate-docs.py --repo-root '$T' 2>&1 | grep -q SNAP-PARSE"
check "and the validator exits non-zero" bash -c "! python3 -B tools/scripts/validate-docs.py --repo-root '$T'"
check "and sync-snapshot --check says the snapshot does not parse" bash -c "python3 -B tools/scripts/sync-snapshot.py --repo-root '$T' --check --quiet 2>&1 | grep -q 'SNAPSHOT.yaml does not parse'"
check "and exits non-zero" bash -c "! python3 -B tools/scripts/sync-snapshot.py --repo-root '$T' --check --quiet"
cp SNAPSHOT.yaml before.yaml
check "and plain sync-snapshot refuses to write" bash -c "! python3 -B tools/scripts/sync-snapshot.py --repo-root '$T' --quiet"
check "and leaves the file as it was" cmp -s SNAPSHOT.yaml before.yaml
echo "test-snapshot-parse: $((n - failures))/$n passed"
[ "$failures" -eq 0 ]
