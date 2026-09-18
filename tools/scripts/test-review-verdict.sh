#!/usr/bin/env bash
# The REVIEW gate on a passing test note, run end to end (project-os-dev
# ISS-0025): only approved passes; changes-requested and any other word fail.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
failures=0; n=0
mkdir -p "$T/docs/tests"
printf 'items:\n  tests:\n    TST-0001: { file: "docs/tests/TST-0001-A.md", status: passing }\n' > "$T/SNAPSHOT.yaml"
case_() { # case_ <description> <verdict> <expect: error|clean>
  n=$((n + 1))
  printf -- '---\ntype: "[[test]]"\nid: TST-0001\ntitle: "A"\nstatus: passing\nowner: user:edwin\ncreated: 2026-09-18\nupdated: 2026-09-18\nreviewed_by: model:x\nreview_date: 2026-09-18\nreview_verdict: "%s"\n---\n# A\n' "$2" > "$T/docs/tests/TST-0001-A.md"
  out="$(python3 "$HERE/validate-docs.py" --repo-root "$T" 2>&1)"
  if grep -q '^ERROR \[REVIEW\] TST-0001' <<<"$out"; then got=error; else got=clean; fi
  if [[ "$got" == "$3" ]]; then echo "  ok   $1"; else echo "  FAIL $1 (got $got)"; failures=$((failures + 1)); fi
}
case_ "approved passes" approved clean
case_ "changes-requested fails" changes-requested error
case_ "a made-up word fails" plan-accepted error
case_ "free text fails" "looks fine to me" error
echo "test-review-verdict: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]
