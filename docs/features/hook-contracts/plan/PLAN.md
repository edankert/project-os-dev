# Plan: Hook contract definitions and tool-specific implementations

## Sequence
1. TASK-0004: Define HOOKS.md with all hook contracts (spec first)
2. TASK-0005: Implement Claude Code hooks (scripts + hooks.json)
3. TASK-0006: Create/update adapter-sync skill to include hook regeneration

## Approach
- Hook contracts are defined as specifications (trigger, check, failure behaviour) independent of any tool
- Claude Code is the first implementation target (most mature hook system)
- Each hook script reads SNAPSHOT.yaml and relevant note frontmatter to perform checks
- Scripts use standard exit codes: 0 = pass, non-zero = block/warn
- Hooks complement skills — skills guide the agent through the full workflow, hooks enforce critical gates
