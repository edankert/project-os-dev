---
type: "[[risk]]"
id: RISK-0004
title: "The harness reads the user's session transcripts, so anything it prints can carry private content into the repo"
status: closed
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "risk scan 2026-09-21"]
likelihood: low
impact: high
mitigation: ["The transcript benchmark prints counts and recalls only, never transcript text", "The reference note and any committed result carry no session content", "Transcripts are read in place and never copied into the repo"]
related: [FEAT-0038, TASK-0152, TASK-0155, REQ-0032]
---

# The harness reads the user's session transcripts

## Description

The transcript benchmark opens the stored session records under `~/.claude/projects/<repo-path>/`. Those files hold whatever was typed and whatever was read during a session, which can include credentials, personal data and the contents of files from outside this repo. The harness itself needs none of that — it needs which notes were opened and when — but it is standing next to all of it, and a later row that printed a session's prompt text to make the table more readable would move that content into the terminal, into a committed reference note, and into git.

The hazard is low-likelihood because nothing in the design wants that content. It is high-impact because a credential committed to a repo is not undone by deleting the line.

## Mitigation

- The transcript benchmark reports counts, recalls and a short session identifier. Never prompt text, never file contents, never a path outside the repo. This is a Definition-of-Done line on TASK-0152 and again on TASK-0155.
- Transcripts are read where they are. Nothing copies them into the repo, not even a filtered extract.
- The reference note recording the first run is reviewed for session content before it is committed.

## Triggers

- A change that prints, logs or stores any transcript field other than a note path, a timestamp or a session identifier.
- A proposal to check a transcript-derived fixture into the repo so the benchmark is reproducible.

## The rest of the scan, recorded as a negative

Run against the triggers in `tools/instructions/LIFECYCLE.md`, "Risk scan triggers", for both deliverables:

- **New external dependency or version constraint:** none. Both scripts are standard library only, and that is a Definition-of-Done line on TASK-0153.
- **New required env var or configuration surface:** none. The ranker takes a query and a budget; the harness takes no arguments for its default run. `TYPESAFE_API_KEY` belongs to the reranker that is explicitly out of scope, and nothing here reads it.
- **Directory layout or artifact path change:** none. Two new files in `tools/scripts/`, no new output directory. If a future change has the harness write a results file, that is a new trigger.
- **Runtime increase or a new long-running step:** none, measured. The ranker answers in 0.9 ms once warm; the git and snapshot benchmarks take a few seconds and the transcript benchmark 2.1 s, against `validate-docs.sh` at 5.31 s. **The reason this stays a negative is that nothing calls the harness automatically** — it is not in the pre-commit hook and not in `validate-docs.sh`, which is a Definition-of-Done line on TASK-0150 and TASK-0153. Wiring it into either gate would make this a real trigger.
- **Security, credential or licence exposure:** the transcript reading above, which is why this note exists.
