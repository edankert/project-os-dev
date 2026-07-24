#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [[ $# -lt 1 ]]; then
  echo "Usage: bash tools/agents/start-change.sh \"Short Description\""
  exit 2
fi

TITLE="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHANGES_DIR="$REPO_ROOT/docs/changes"
TODAY="$(date -u +%Y%m%d)"
TODAY_HUMAN="$(date -u +%Y-%m-%d)"
SLUG="$(printf '%s' "$TITLE" | tr '[:space:]' '-' | tr -cd '[:alnum:]-' | sed 's/--*/-/g' | sed 's/^-//; s/-$//')"

if [[ -z "$SLUG" ]]; then
  echo "ERROR: title produced an empty slug"
  exit 2
fi

mkdir -p "$CHANGES_DIR"

BASE_ID="CHG-${TODAY}-${SLUG}"
FILE="$CHANGES_DIR/${BASE_ID}.md"
i=1
while [[ -e "$FILE" ]]; do
  FILE="$CHANGES_DIR/${BASE_ID}-${i}.md"
  i=$((i + 1))
done

ID="$(basename "$FILE" .md)"

cat > "$FILE" <<EOF
---
type: "[[change]]"
id: ${ID}
title: "${TITLE}"
status: draft
owner: unassigned
created: ${TODAY_HUMAN}
updated: ${TODAY_HUMAN}
source: []
commit: ""
pr: ""
impacts: []
issues: []
features: []
related: []
---

# ${TITLE}

## Summary
<what changed and why>

## Impact
- <affected areas/flows/workflows>

## Documentation Coverage (All Types Considered)
Set each item to one of: \`updated\`, \`new\`, \`not-applicable\`, \`deferred\`.

- features: pending
- requirements: pending
- tasks: pending
- issues: pending
- tests: pending
- workflows: pending
- decisions: pending
- risks: pending
- changes: new
- snapshot: pending

## Follow-ups
- [ ] <doc updates / regressions / cleanup>
EOF

echo "Created: ${FILE}"
echo "Next steps:"
echo "1) Fill Documentation Coverage values (no 'pending')."
echo "2) Update SNAPSHOT.yaml."
echo "3) Implement changes."
echo "4) Run: bash tools/agents/check-docs-first.sh"
