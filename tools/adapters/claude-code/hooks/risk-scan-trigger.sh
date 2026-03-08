#!/bin/bash
# HC-005: Risk Scan Trigger
# Claude Code PostToolUse hook for Write/Edit tools
#
# Warns when package manifests, env files, or CI configs are modified,
# reminding the agent to run a risk scan.
# Advisory only — does not block.
#
# Exit 0 = allow (always)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

case "$FILE_PATH" in
  *package.json|*package-lock.json|*Cargo.toml|*Cargo.lock|*requirements.txt|*go.mod|*go.sum|*Gemfile|*Gemfile.lock|*pom.xml|*build.gradle*)
    echo "NOTE: Package manifest changed ($FILE_PATH). Run risk-scan skill to assess new dependency risks (HC-005)."
    ;;
  *.env|*.env.example|*.env.local|*.env.production*)
    echo "NOTE: Environment config changed ($FILE_PATH). Run risk-scan skill to assess env var exposure (HC-005)."
    ;;
  *.github/workflows/*|*.gitlab-ci.yml|*Jenkinsfile|*Dockerfile|*docker-compose*)
    echo "NOTE: CI/CD or infrastructure config changed ($FILE_PATH). Run risk-scan skill to assess deployment risks (HC-005)."
    ;;
esac

exit 0
