#!/usr/bin/env bash
# review-packet.py against a throwaway repo whose answers are known
# (project-os-dev TASK-0126, TASK-0129). Each assertion names what the packet
# must or must not carry; a packet that silently widens or narrows the scope is
# the failure this guards.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/review-packet.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
failures=0
n=0
check() { # check <description> <command...>
  n=$((n + 1))
  if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi
}

R="$T/repo"
mkdir -p "$R/docs/features/x/plan/tasks" "$R/src" "$R/tests" "$R/app/schemas"
cd "$R" && git init -q && git config user.email t@t && git config user.name t
cat > docs/features/x/FEAT-0001-X.md <<'EOF'
---
type: "[[feature]]"
id: FEAT-0001
title: "The widget stops"
goal: "The widget stops when asked."
tasks: [TASK-0001, TASK-0002]
---

# The widget stops

## Scope
- SCOPE-DELTA: the widget stops from two sources.

## Acceptance
- CRITERION-ALPHA: the widget stops within one second.

## Verification
- `make test`, 2026-09-18: 12 passed.
EOF
cat > docs/features/x/plan/tasks/TASK-0001-A.md <<'EOF'
---
id: TASK-0001
tests: [TST-0007]
---
EOF
mkdir -p docs/tests
printf -- '---\nid: TST-0008\ncovers: ["[[FEAT-0001-X]]"]\n---\n' > docs/tests/TST-0008-Covers.md
echo base > src/other.py
git add -A && git commit -qm "Initial"
echo 'def stop(): return GUARD_ONE' > src/widget.py
echo 'assert stop()' > tests/test_widget.py
echo '{"generated": true}' > app/schemas/1.json
echo "note change" >> docs/features/x/plan/tasks/TASK-0001-A.md
git add -A && git commit -qm "TASK-0001: the widget can stop"
echo 'UNRELATED_CHANGE' >> src/other.py
git add -A && git commit -qm "Something else" -m "Mentions FEAT-0001 only in passing."
ROUND1="$(git rev-parse HEAD)"

P="$T/review-packet-FEAT-0001-r1.md"
python3 "$SCRIPT" FEAT-0001 --repo-root "$R" --out "$P" --claim "CLAIM-BETA holds" >/dev/null 2>"$T/err"
check "a packet is written" test -s "$P"
check "it carries the acceptance criterion word for word" grep -q "CRITERION-ALPHA: the widget stops within one second." "$P"
check "it carries the author's claim" grep -q "CLAIM-BETA holds" "$P"
check "it carries what the note's Scope says the feature delivers" grep -q "SCOPE-DELTA" "$P"
check "it names the linked test from the task" grep -q "TST-0007" "$P"
check "it names the test whose covers: names the feature" grep -q "TST-0008" "$P"
check "it carries the author's last full run" grep -q "12 passed" "$P"
check "it carries the source diff of the task's commit" grep -q "GUARD_ONE" "$P"
check "it flags the test file" grep -q "tests/test_widget.py\`  (test)" "$P"
check "it leaves the notes out of the diff" bash -c "! grep -q 'note change' '$P'"
check "it leaves out a commit naming the feature only in its body" bash -c "! grep -q 'UNRELATED_CHANGE' '$P'"
check "it leaves the generated file out of the diff" bash -c "! grep -q '\"generated\": true' '$P'"
check "it lists the generated file as left out" grep -q "app/schemas/1.json" "$P"
check "a small diff stays inline, with no companion file" test ! -e "${P%.md}.diff"
check "round one states a budget of 40" grep -q "Budget: 40 tool calls" "$P"

check "a fourth author claim is refused" bash -c "! python3 '$SCRIPT' FEAT-0001 --repo-root '$R' --out '$T/x.md' --claim a --claim b --claim c --claim d"
check "a feature no commit names is refused" bash -c "cd '$R' && sed 's/FEAT-0001/FEAT-0009/; s/TASK-0001, TASK-0002/TASK-0009/' docs/features/x/FEAT-0001-X.md > docs/features/x/FEAT-0009-Y.md && ! python3 '$SCRIPT' FEAT-0009 --repo-root '$R' --out '$T/y.md'"
rm -f "$R/docs/features/x/FEAT-0009-Y.md"

# A large diff goes to a companion file with an index.
python3 - "$R/src/big.py" <<'EOF'
import sys
open(sys.argv[1], "w").write("".join("line_%d = %d\n" % (i, i) for i in range(600)))
EOF
cd "$R" && git add -A && git commit -qm "TASK-0002: a large change"
P2="$T/review-packet-FEAT-0001-r1b.md"
python3 "$SCRIPT" FEAT-0001 --repo-root "$R" --out "$P2" >/dev/null 2>&1
check "a large diff is written to a companion .diff file" grep -q "line_599" "${P2%.md}.diff"
check "the packet indexes it instead of inlining it" bash -c "grep -q '| \`src/big.py\` |' '$P2' && ! grep -q 'line_599' '$P2'"

# Round two: the review section and the fixes since round one, nothing else.
cd "$R" && printf '\n## Review\n- F1 refuted: FINDING-GAMMA.\n' >> docs/features/x/FEAT-0001-X.md
echo 'def stop(): return GUARD_FIXED' > src/widget.py && git add -A && git commit -qm "TASK-0002: fix F1"
P3="$T/review-packet-FEAT-0001-r2.md"
python3 "$SCRIPT" FEAT-0001 --repo-root "$R" --round 2 --since "$ROUND1" --out "$P3" >/dev/null 2>&1
check "round two carries round one's finding" grep -q "FINDING-GAMMA" "$P3"
check "round two carries the fix" bash -c "grep -q GUARD_FIXED '$P3' '${P3%.md}.diff' 2>/dev/null"
check "round two states a budget of 15" grep -q "Budget: 15 tool calls" "$P3"
check "round two carries no acceptance criteria to re-check" bash -c "! grep -q 'CRITERION-ALPHA' '$P3'"
check "round two without --since is refused" bash -c "! python3 '$SCRIPT' FEAT-0001 --repo-root '$R' --round 2 --out '$T/z.md'"

# A feature whose notes and code are in different repos (project-os-dev holds the
# notes for project-os's code). Without --code-root the diff filter strips
# everything such a feature touched and the packet arrives empty, which sent four
# reviewers to read prose in place of code (FEAT-0034 review, 2026-09-20).
NOTES="$T/notes"; CODE="$T/code"
mkdir -p "$NOTES/docs/features/y" "$CODE/src"
(cd "$NOTES" && git init -q && git config user.email t@t && git config user.name t)
cat > "$NOTES/docs/features/y/FEAT-0009-Y.md" <<'EOF'
---
type: "[[feature]]"
id: FEAT-0009
title: "The code lives elsewhere"
goal: "Its notes are here and its code is not."
tasks: []
---

# The code lives elsewhere

## Acceptance

- It works.
EOF
(cd "$NOTES" && git add -A && git -c core.hooksPath=/dev/null commit -qm "FEAT-0009: the note only")
(cd "$CODE" && git init -q && git config user.email t@t && git config user.name t)
printf 'seed\n' > "$CODE/README.md"
(cd "$CODE" && git add -A && git -c core.hooksPath=/dev/null commit -qm "seed")
BASE="$(cd "$CODE" && git rev-parse HEAD)"
printf 'def go():\n    return 1\n' > "$CODE/src/go.py"
(cd "$CODE" && git add -A && git -c core.hooksPath=/dev/null commit -qm "FEAT-0009: the code")

out="$(python3 "$SCRIPT" FEAT-0009 --repo-root "$NOTES" --out "$T/p9.md" 2>&1)"; rc=$?
check "a packet with no source diff is refused" test "$rc" -ne 0
check "the refusal names --code-root" grep -q -- "--code-root" <<<"$out"
out="$(python3 "$SCRIPT" FEAT-0009 --repo-root "$NOTES" --allow-empty-diff --out "$T/p9.md" 2>&1)"
check "--allow-empty-diff lets a documentation-only feature through" test -f "$T/p9.md"

python3 "$SCRIPT" FEAT-0009 --repo-root "$NOTES" --code-root "$CODE" --range "$BASE"..HEAD --out "$T/p10.md" >/dev/null 2>&1
P10="$T/p10.md"
check "--code-root takes the diff from the code repo" grep -q "src/go.py" "$P10"
check "and the packet says where the code is" grep -q "the code this feature changed is in" "$P10"

echo "test-review-packet: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]
