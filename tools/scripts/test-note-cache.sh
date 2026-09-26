#!/usr/bin/env bash
# The note cache and note index (project-os-dev ISS-0093, TASK-0169): a note is
# parsed once, kept on disk keyed by path, size and mtime, and re-read when it
# changes; the cache never changes what the validator reports. Fixtures under a
# tempdir, and the cache under its own TMPDIR. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export TMPDIR="$TMP/cache-home"; mkdir -p "$TMPDIR"
unset PROJECT_OS_NO_CACHE
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; mkdir -p "$R/docs/issues" "$R/docs/decisions"
N="$R/docs/issues/ISS-0001-One.md"
printf -- '---\nid: ISS-0001\nstatus: open\ncreated: 2026-09-01\nrelated: ["[[ADR-0002]]"]\n---\n# One\n\n## Why\n\nSee ADR-0002 and TASK-0003.\n' > "$N"
printf -- '---\nid: ADR-0002\nstatus: accepted\n---\n# Two\n' > "$R/docs/decisions/ADR-0002-Two.md"

# `status` prints the frontmatter status; with FAIL_PARSE=1 the real parser
# raises, so an answer can only have come from the cache.
cat > "$TMP/status.py" <<'PY'
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
if os.environ.get("FAIL_PARSE") == "1":
    def boom(path): raise SystemExit("parsed")
    vd._parse_frontmatter_strict = boom
fm = vd.parse_frontmatter(Path(sys.argv[2]))
print(fm["status"], type(fm["created"]).__name__)
PY
st() { python3 "$TMP/status.py" "${VD:-$HERE/validate-docs.py}" "$N" 2>&1; }
cachefiles() { find "$TMPDIR/project-os-note-cache" -name '*.json' 2>/dev/null | wc -l | tr -d ' '; }

# A date is a date under PyYAML and a string under the fallback parser; the
# cache must hand back whichever type the parse produced.
o="$(PROJECT_OS_NO_CACHE=1 st)"; T="${o#open }"
check "PROJECT_OS_NO_CACHE=1 parses and writes no cache" "$([[ "$o" == "open $T" && $(cachefiles) -eq 0 ]]; echo $?)" "$o"
o="$(st)"
check "a first run parses and leaves a cache file" "$([[ "$o" == "open $T" && $(cachefiles) -eq 1 ]]; echo $?)" "$o"
o="$(FAIL_PARSE=1 st)"
check "a second run answers from the cache, the value's type kept" "$([[ "$o" == "open $T" ]]; echo $?)" "$o"

# An edit that keeps the size: only the mtime tells the cache the note changed.
sed -i.bak 's/^status: open$/status: shut/' "$N"; rm -f "$N.bak"
touch -t 202609020000 "$N"
o="$(st)"
check "an edit of the same size is re-read (mtime is in the key)" "$([[ "$o" == "shut $T" ]]; echo $?)" "$o"
printf '\nMore.\n' >> "$N"
o="$(st)"
check "an edit that changes the size is re-read" "$([[ "$o" == "shut $T" ]] && FAIL_PARSE=1 st | grep -q '^shut'; echo $?)" "$o"

# A change to the validator discards every cached entry.
mkdir -p "$TMP/vd2"; cp "$HERE/validate-docs.py" "$TMP/vd2/"; echo "# changed" >> "$TMP/vd2/validate-docs.py"
o="$(VD="$TMP/vd2/validate-docs.py" FAIL_PARSE=1 st)"
check "a changed validator does not trust the old cache" "$(printf '%s' "$o" | grep -q '^parsed'; echo $?)" "$o"

# A corrupt cache file is ignored, not believed.
for f in "$TMPDIR"/project-os-note-cache/*.json; do printf '{"tag": ' > "$f"; done
o="$(st)"
check "a corrupt cache file is ignored" "$([[ "$o" == "shut $T" ]]; echo $?)" "$o"

# The note index: records and backlinks, from frontmatter and body.
o="$(python3 "$HERE/note-index.py" --repo-root "$R" --json ISS-0001)"
check "the index gives id, status, path, links and headings" "$(python3 -c 'import json,sys; r=json.loads(sys.argv[1])["ISS-0001"]; sys.exit(0 if r["status"]=="shut" and r["path"]=="docs/issues/ISS-0001-One.md" and r["links"]==["ADR-0002","TASK-0003"] and r["headings"]==["One","Why"] and r["archived"] is False else 1)' "$o"; echo $?)" "$o"
check "--links-to inverts the links, body links included" "$([[ "$(python3 "$HERE/note-index.py" --repo-root "$R" --links-to ADR-0002)" == "ISS-0001" && "$(python3 "$HERE/note-index.py" --repo-root "$R" --links-to TASK-0003)" == "ISS-0001" ]]; echo $?)"
python3 "$HERE/note-index.py" --repo-root "$R" ISS-0404 >/dev/null; code=$?
check "an unknown id exits 1" "$([[ $code -eq 1 ]]; echo $?)"

# NOTE-FRONTMATTER reuses the frontmatter parse when PyYAML read the same
# text, so a broken note must still be reported, cold and warm. ISS-0004 parses
# as frontmatter, but the check splits at the first `---` after the opening
# one, inside its quoted title, and has always reported it; it still does.
if python3 -c 'import yaml' 2>/dev/null; then
  B="$TMP/broken"; mkdir -p "$B/docs/issues"; printf 'version: 1\nitems: {}\n' > "$B/SNAPSHOT.yaml"
  printf -- '---\nid: ISS-0003\ntitle: "Retire "walk" from it"\nstatus: open\n---\n# Three\n' > "$B/docs/issues/ISS-0003-Three.md"
  printf -- '---\nid: ISS-0004\ntitle: \"a---b\"\nstatus: open\n---\n# Four\n' > "$B/docs/issues/ISS-0004-Four.md"
  nf() { python3 - "$HERE/validate-docs.py" "$B" <<'PY2'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
r = vd.Report(); vd.validate_frontmatter_parses(Path(sys.argv[2]), r)
lines = [l for l in r.errors + r.warnings if "NOTE-FRONTMATTER" in l]
print(" ".join(n for n in ("ISS-0003", "ISS-0004") if any(n in l for l in lines)), len(lines))
PY2
  }
  cold_nf="$(nf)"; warm_nf="$(nf)"; off_nf="$(PROJECT_OS_NO_CACHE=1 nf)"
  check "the same notes are reported cold, warm and uncached, including one only the check's own split breaks" \
    "$([[ "$cold_nf" == "ISS-0003 ISS-0004 2" && "$warm_nf" == "$cold_nf" && "$off_nf" == "$cold_nf" ]]; echo $?)" "cold '$cold_nf' warm '$warm_nf' off '$off_nf'"
fi

# The cache never changes what the validator says: off, cold and warm agree on
# this template's own notes.
ROOT="$(cd "$HERE/../.." && pwd)"
off="$(cd "$ROOT" && PROJECT_OS_NO_CACHE=1 python3 "$HERE/validate-docs.py" 2>&1)"
rm -rf "$TMPDIR/project-os-note-cache"
cold="$(cd "$ROOT" && python3 "$HERE/validate-docs.py" 2>&1)"
warm="$(cd "$ROOT" && python3 "$HERE/validate-docs.py" 2>&1)"
check "validator output: cache off, cold and warm are identical" "$([[ "$off" == "$cold" && "$cold" == "$warm" ]]; echo $?)" "$(diff <(printf '%s\n' "$off") <(printf '%s\n' "$warm") | head -5)"

echo "test-note-cache: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]
