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

# The note is scaffolded from the one template the repo carries, never from a
# copy embedded here: an embedded copy drifts (it shipped `status: draft`, a
# value STATUSES.md does not allow for a change note; project-os-dev ISS-0048).
TEMPLATE="$REPO_ROOT/docs/__templates__/change.md"
if [[ ! -f "$TEMPLATE" ]]; then
  echo "start-change: $TEMPLATE not found; cannot scaffold a change note." >&2
  exit 1
fi
sed -e "s|^id: .*|id: ${ID}|" \
    -e "s|^title: .*|title: \"${TITLE}\"|" \
    -e "s|^created: .*|created: ${TODAY_HUMAN}|" \
    -e "s|^updated: .*|updated: ${TODAY_HUMAN}|" \
    -e "s|^# <Change Title>|# ${TITLE}|" \
    "$TEMPLATE" > "$FILE"

echo "Created: ${FILE}"
echo "Next steps:"
echo "1) Fill the Documentation Coverage values and link the note from the issues and features it affects."
echo "2) Run: bash tools/agents/check-docs-first.sh (a change note is due at close-out when behaviour, paths or contracts change; LIFECYCLE.md)"
