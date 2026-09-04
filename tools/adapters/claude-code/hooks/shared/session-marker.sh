# Where the "this session wrote something" marker lives. Sourced, not run.
#
# Stated once here because close-out-check.sh writes to the same path that
# session-touch.sh creates, and two copies of a path formula that must agree is
# the drift ISS-0048 spent twelve passes counting.
#
# The marker is keyed by the session and by the project directory, so one
# session working in two repos gets one marker per repo. It is a zero-byte file
# in the temp directory: session state, not project state, and nothing outlives
# the machine's temp cleanup. Nothing reads its contents.

# session_marker <session-id> <project-dir> -> absolute path on stdout
session_marker() {
  local session dir tmp key
  session=$(printf '%s' "$1" | tr -cd '[:alnum:]._-')
  dir=$2
  [ -n "$session" ] || return 1
  tmp=${TMPDIR:-/tmp}
  tmp=${tmp%/}
  # cksum is POSIX and present on macOS and Linux; the digest only has to be
  # stable and collision-free enough to separate a handful of repo paths.
  key=$(printf '%s' "$dir" | cksum | tr -cd '[:digit:]')
  printf '%s/project-os-touched-%s-%s' "$tmp" "$session" "$key"
}
