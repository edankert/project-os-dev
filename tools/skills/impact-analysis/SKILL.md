---
type: skill
id: SKILL-IMPACT-ANALYSIS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
tags: [skills, impact-analysis, requirements, conflict-detection]
---

# Skill: Impact analysis

## When to use
- A new requirement (`REQ-*`) is being created or significantly modified.
- A new feature (`FEAT-*`) is being scaffolded that touches an existing area of the codebase.
- An issue (`ISS-*`) is filed that may affect features constrained by existing requirements.
- Any time a change may interact with or contradict existing documented requirements.

## Inputs
- The new or modified item (requirement, feature, or issue).
- `../../../SNAPSHOT.yaml` (for the full link graph).
- Relevant notes under `../../../docs/` (requirements, features).

## Outputs
- A list of potentially affected features and their existing requirements.
- Any identified tensions or contradictions between the new item and existing requirements.
- If conflicts are found: a summary presented to the user with resolution options.
- If no conflicts: explicit confirmation that no tensions were identified.

## Checklist

### 1. Identify the impact surface
1. From the new item, identify which features it touches:
   - New requirement: which features will implement it? (Check `implements` or intended feature links.)
   - New feature: which existing features share the same component, module, or user-facing area?
   - New issue: which features does it impact? (Check `features` in the issue.)
2. List all identified features by ID.

### 2. Gather existing constraints
For each identified feature:
1. Read its note and list all linked requirements (`requirements` in frontmatter).
2. For each linked requirement, read the requirement note — specifically `acceptance` criteria and any scope/constraint language.
3. Also check for linked ADRs (`decisions`) that may constrain the feature's design.

### 3. Detect tensions
Compare the new item's intent against each existing constraint:
1. **Direct contradiction**: Does the new item require behaviour that an existing requirement explicitly prohibits or conflicts with?
   - Example: New REQ says "add mandatory verification step" vs existing REQ says "minimise onboarding steps."
2. **Scope overlap**: Does the new item partially overlap an existing requirement's scope in a way that creates ambiguity?
   - Example: Both requirements define how error messages should be formatted, but with different rules.
3. **Resource conflict**: Does the new item compete with existing requirements for the same limited resource (UI space, performance budget, API rate limits)?
4. **Phase conflict**: Does the new item belong to a different phase than the feature it targets?

### 4. Report findings
If **no tensions** found:
- State: "Impact analysis complete. No conflicts identified with existing requirements on [list of features checked]."
- Proceed with the originating skill (feature-scaffold, issue-intake, etc.).

If **tensions found**:
- Present each tension with:
  - The conflicting items (IDs and titles)
  - The nature of the conflict (direct contradiction, scope overlap, resource conflict, phase conflict)
  - The specific language in each requirement that creates the tension
- Propose resolution options (at minimum):
  1. Supersede the older requirement (create new REQ, mark old as `retired`, create ADR documenting the change)
  2. Scope the new requirement to avoid overlap (e.g., apply to a subset of users/tiers)
  3. Accept the contradiction and document it as a known trade-off (create ADR)
- **STOP and wait for user decision.** Do not proceed with implementation until the conflict is resolved.

### 5. Document the resolution
Once the user chooses a resolution:
1. Update affected requirement notes (scope changes, retirement, etc.).
2. Create an ADR if the resolution represents a significant design decision.
3. Update `../../../SNAPSHOT.yaml` with any new/modified items and relationships.
4. Proceed with the originating skill.
