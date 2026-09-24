---
type: "[[reference]]"
id: REFERENCE-AI-MODERNIZATION-2026-09-23
title: "AI modernization: what the in-flight projects already prove and what to implement next"
status: active
owner: user:edwin
created: 2026-09-23
updated: 2026-09-23
scope: "project"
source:
  - "https://claude.com/blog/how-to-prepare-for-ai-driven-code-modernization-projects"
  - "Read-only inspection of local fleet repositories and focused execution, 2026-09-23"
related: ["[[FEAT-0020-Typed-Evidence]]", "[[ADR-0014-Evidence-Is-Typed-And-Checkable]]", "[[ADR-0017-Claims-About-Working-Software-Are-Derived]]", "[[ADR-0022-Conventions-Before-Types]]", "[[ISS-0081-Observable-Criteria]]"]
---

# AI modernization: evidence from the projects already in flight

## Finding

The in-flight projects already demonstrate several mechanisms the article recommends. Your Trainer's Android-to-iOS port is the strongest modernization example. Sudoku demonstrates an executable requirement check. Your Health and Deck show why passing tests alone cannot settle a claim. The cockpit already stores platform-specific verification events and derives release gates from them.

The first recommendation in the conversation was incomplete: it proposed a new pilot without checking these projects. The better next step is to use their existing work and evidence. First assemble a reviewable report from the current records. Then extend evidence recording only where that report exposes a concrete missing connection.

This is evidence that specific mechanisms exist and catch specific failures. It is not a controlled measurement of project-os's overall productivity benefit or proof of enterprise regulatory compliance.

## Article assessment

Anthropic's [guide, published 23 September 2026](https://claude.com/blog/how-to-prepare-for-ai-driven-code-modernization-projects), argues that faster code generation shifts the bottleneck toward organizational readiness. Its six steps cover the target, a correctness certificate, promotion policy, prerequisites, workflow development and a small end-to-end run before scaling. It distinguishes version upgrades, behaviour-preserving rewrites and rebuilds that change behaviour. It recommends source-grounded discovery, executable checks, independent review and explicit treatment of review capacity and access.

This reinforces project-os's requirements, decisions, evidence gates, workflows and release records. Treat the article as practitioner guidance from a vendor. It supplies a useful design comparison, not independent proof of project-os's effectiveness or a measured speedup to reuse in product claims.

## Scope and evidence standard

The assessment screened the focus sections of all 13 local repositories carrying `SNAPSHOT.yaml`. It then inspected five projects with relevant implementation or verification work. Repository heads below identify the inspected state; historical measurements remain dated claims in their source notes.

| Repository | Branch and head | Working tree at inspection | Evidence used |
|---|---|---|---|
| your-trainer | `main`, `c0ee605e` | Clean | Parity scope, accepted differences, changed target, release records, fresh walk and gate queries |
| project-os-cockpit | `main`, `abd73db` | Clean | Ledger and release code, rebuilt renderer, 93 focused tests |
| your-sudoku | `feat/scanner-digit-cnn`, `58d63e7` | Existing untracked Python cache | Product-ID requirement check, fresh positive run and two deliberate defects on temporary copies |
| your-health | `main`, `496934c` | Existing untracked `.design-headers/` and `.design-sections/` | Review record, coefficient tests, outstanding device check; no app test rerun |
| project-os-deck | `main`, `5b789fb` | Clean | Review and adequacy records, outstanding renderer checks; no renderer or smoke rerun |

In this report, **executed** means run during this assessment. **Recorded** means inspected in a dated note or test source. Neither reading a note nor finding a test file is counted as a fresh passing run. No application release verdict was written.

## Evidence from the in-flight projects

### Your Trainer already has the modernization case

[PHASE-019](../../../your-trainer/docs/phases/PHASE-019-iOSParity.md) defines Android as the behavioural reference for the native iOS port. Its input bundle combines source, scope, design rules, issue history and acceptance checks. The [parity matrix](../../../your-trainer/docs/features/ios-parity/PARITY_MATRIX.md) maps surfaces to implementation status. The [divergence ledger](../../../your-trainer/docs/features/ios-parity-verification/DIVERGENCE_LEDGER.md) distinguishes defects from intentional platform differences.

This is also evidence of a failed verification approach. The matrix explicitly withdraws its June full-parity claim after July device sessions found missing navigation, incorrect graphs and lifecycle gaps. Presence had been mistaken for behavioural equivalence. The record now requires behaviour to be exercised, and says the remaining old DONE rows have not all been re-audited.

[PHASE-025](../../../your-trainer/docs/phases/PHASE-025-NavigationStructure.md) separately records a change to the Android target during the port. The owner's freeze exception requires both platforms to land together, altered matrix rows to change and screen galleries to regenerate. That is a concrete example of handling a changing target without silently redefining the original parity work.

**Executed on 23 September:** the cockpit's current walk query returned 86 owed Android checks for `REL-0017` and 333 owed iOS checks with no release selected. Every owed row was placed in a sitting. The platform gate query returned `blocked: true` for both platforms. These counts supersede the older 39/327 counts for this observation; they do not rewrite those historical measurements. The gate calls used platform scope without release deselection, so these are not a claim that every row blocks the selected Android release.

[REL-0017](../../../your-trainer/docs/releases/REL-0017-v2.2.0.md) remains a draft Android release. The sampled walk task still names the human walk and broader equivalence audit as outstanding. This is an existing case to finish and measure, not evidence that the migration has shipped successfully.

### The cockpit already implements much of the proposed evidence record

[ledger.py](../../../project-os-cockpit/src/project_os_cockpit/ledger.py) records acceptance events by check, platform and release, with author, method and date. It supports evidence references, invalidation and sealing. Sealed records have integrity checks. [acceptance.py](../../../project-os-cockpit/src/project_os_cockpit/acceptance.py) derives owed checks and gate results; [publication.py](../../../project-os-cockpit/src/project_os_cockpit/publication.py) already assembles release information.

**Executed:** the renderer build succeeded, followed by 93 passing cases across [copied-ledger tests](../../../project-os-cockpit/tests/test_guided_walk_ledger_copy.py), [ledger tests](../../../project-os-cockpit/tests/test_ledger.py) and [ledger-validator tests](../../../project-os-cockpit/tests/test_ledger_validator.py). These include platform separation, invalidation, expired exceptions, sealed-record tampering and selected real Your Trainer procedures emitting the same requests through step and direct-check controls.

The copied-ledger tests assert that the original ledger bytes remain unchanged. They exercise renderer builders through a minimal DOM and replay requests into temporary ledgers. They do not run a rider through the application, prove every procedure equivalent, or supply the outstanding human verdict.

**Implication:** extend the existing release query. A parallel certificate store or independently calculated gate would duplicate working mechanisms.

### Sudoku demonstrates an executable connection from requirement to code

[ISS-0116](../../../your-sudoku/docs/issues/ISS-0116-product-id-alignment-has-no-test.md) records that multiple notes claimed product IDs were aligned while Android and iOS still differed. [TST-0084](../../../your-sudoku/docs/tests/TST-0084-Product-Id-Alignment.md) now invokes [check-product-id.sh](../../../your-sudoku/tools/scripts/check-product-id.sh). The script compares both source literals with the product ID recorded in the requirement and rejects an empty extraction.

**Executed:** the current check passed with `com.yoursudoku.pro` in all three places. On temporary copies, changing the iOS ID to `com.yoursudoku.mismatch` failed with exit 1. Removing the iOS value also failed with exit 1 and an explicit empty-extraction message. The original files were untouched.

This proves source-to-requirement agreement and detection of those two defects. The script does not query either store console, so its printed word “Registered” is not independent evidence of external store configuration.

**Implication:** repeat this approach for a requirement whose truth can be executed. A typed evidence label alone would not have caught the mismatch.

### Your Health demonstrates why the test itself needs independent evidence

[ISS-0177](../../../your-health/docs/issues/ISS-0177-The-Citation-Test-Cannot-Fail-On-A-Wrong-Coefficient.md) records that a deliberate coefficient transposition left the original body tests green. The fix introduced [PublishedBodyTablesTest.kt](../../../your-health/app/src/test/kotlin/com/yourhealth/domain/body/PublishedBodyTablesTest.kt), with expected values transcribed from primary documents and independently reviewed. The issue records which deliberate changes subsequently failed.

This assessment inspected the issue and test source. It did not rerun Gradle or revalidate the underlying publications. The [feature](../../../your-health/docs/features/bmi-and-bmr/FEAT-0116-BMI-And-BMR-Each-Naming-Its-Publisher.md) is at `review`, and [TST-0056](../../../your-health/docs/tests/TST-0056-The-Body-Section-Walked-On-The-FP5.md) is still `ready` for a human device walk.

**Implication:** evidence must identify what an assertion checks. A valid citation, a correct calculation and a visible screen are different claims with different tests.

### Deck demonstrates the boundary of a passing suite

[FEAT-0018](../../../project-os-deck/docs/features/glass-bands/FEAT-0018-Every-Note-Has-A-Place-And-Anything-Visible-Can-Be-Reached.md) remains at `review` with `changes-requested`. Its review records explain how renderer defects survived passing Node tests because those tests did not load the renderer. The record names outstanding smoke checks and a human walk. The snapshot records the last smoke attempt stopping because Docker's daemon was unavailable; that environment condition was not rechecked here.

**Implication:** an evidence report must show “not executed” and its reason separately from passing tests. It must also distinguish a missing test environment from a product decision about what the feature should promise.

## Suggested implementation, in order

These are proposals, not newly scheduled features. FEAT-0038 and PHASE-0008 remain completed. This documentation-only assessment does not re-adopt parked work or authorize a deployment.

| Order | Deliverable and implementation home | Existing material to reuse | Completion evidence |
|---|---|---|---|
| 1 | An export of the current release evidence, implemented in project-os-cockpit alongside `publication.py` and `acceptance.py` | Your Trainer `REL-0017`, platform ledgers, requirements, linked tests and review records | Export and existing release page agree for the same scope; no missing or unknown result becomes a pass |
| 2 | A narrow producer of machine-readable execution evidence, planned here as a proposed slice of FEAT-0020 and implemented in the template's test runner | `run-tests.py`, existing CI artifacts, Sudoku's executable criterion, current ledger evidence | A rerun identifies the tested revision and actual command outcome; stale or unrelated evidence cannot settle the sampled claim |
| 3 | A modernization workflow convention, implemented in the template and tried on the existing Your Trainer parity work | PHASE-019's input bundle, parity matrix, divergence ledger and PHASE-025's freeze exception | Another maintainer can identify the fixed target, permitted differences, owed verification and owner decisions without reconstructing the conversation |
| 4 | Measurement of one existing release's path through review and promotion | Existing release, test and review timestamps, plus explicitly recorded human time | Dated observations separate execution time, review effort and waiting; no productivity multiplier inferred without a comparator |

### First increment: derive the report before extending the schema

Proposed inputs are repository, release, platform and candidate revision. The report should expose the source revision and dirty-tree state, selected scope, linked criteria, recorded reviews, automated execution evidence, manual verdicts, exceptions and remaining decisions. Each result needs a source pointer. Unsupported or absent data stays unknown.

Use the existing gate and release selection functions. Reuse the working/sealed ledger distinction and existing invalidation rules. Do not decide freshness from a date alone. A result earned on another build or platform cannot silently become evidence for the candidate.

Keep verification and authority distinct. A report can show that known checks are settled. Permission to publish still comes from the project's recorded release workflow and owner. Derive CI conditions from executable configuration or point to it; do not copy thresholds into another authored checklist.

The first acceptance cases should use the failures already found:

- An Android pass must not settle the corresponding iOS check.
- An exception that expired with an earlier release must remain owed.
- Missing CI evidence for the candidate must read unknown, even if a note says tests passed.
- A skipped renderer run must remain visible beside passing unit tests.
- An invalidated check must return to the owed set.
- A report must agree with the existing release gate for the same selected scope.
- Source edits, test-definition edits or a dirty tested tree must prevent reuse of an apparently matching commit result without an explicit content identity.

Build the report as a query first. Add a UI surface only if the existing release page cannot present the result clearly. Proposed code changes need their own preflight notes before implementation.

### Second increment: make FEAT-0020 earn its scope

[[FEAT-0020-Typed-Evidence]] is backlog and [[ADR-0014-Evidence-Is-Typed-And-Checkable]] remains proposed. The existing acceptance ledger already solves part of the problem the July proposal described. Start by mapping what it covers and what executable evidence still lacks.

The initial candidate is a runner-produced record containing the command identity, repository revision or tested-content identity, relevant platform/environment, time, outcome and artifact reference. CI should provide its own run identity. Human observations keep their separate provenance. A token written by the implementing agent must not be presented as independently executed evidence.

Do not retrofit historical checkboxes or introduce a universal evidence score. The Sudoku and Health cases show that evidence type and a green result do not establish test adequacy. Preserve the existing requirement to demonstrate that the guarding test detects the defect.

### Boundaries and decisions

[[ADR-0017-Claims-About-Working-Software-Are-Derived]] deliberately avoids duplicating executable gate configuration. A derived report respects that boundary. An authored gate manifest would require reconsidering it explicitly. [[ADR-0022-Conventions-Before-Types]] supports using existing note types until a convention demonstrably fails.

The fleet supports documenting a promotion workflow now. It does not yet justify automatic production promotion based on an agent's confidence, a new hosting service, or an enterprise approval subsystem. The article's transcript-traceability suggestion also needs a privacy decision before implementation: source paths or protected references are preferable to copying raw conversations into project notes.

No new dependency, configuration surface, behavioural contract or runtime path was introduced by this assessment. The proposed implementations need their own impact and risk checks when adopted.

## Reproduction and validation

Run these commands in the named repositories. The results below were observed on 23 September 2026, not inferred from historical test counts.

| Repository | Command or probe | Observed result |
|---|---|---|
| your-sudoku | `bash tools/scripts/check-product-id.sh` | Exit 0; both source IDs agree with the requirement |
| your-sudoku | Copy the two source files and REQ-0109 to a temporary root; run the same script with that root after changing the Swift ID, then after emptying its array | Both expected exit-1 results observed; mismatch and missing extraction named |
| project-os-cockpit/desktop | `npm run build` | Exit 0 |
| project-os-cockpit | `.venv/bin/python -m pytest -q tests/test_guided_walk_ledger_copy.py tests/test_ledger.py tests/test_ledger_validator.py` | 93 passed in 4.58 seconds |
| project-os-cockpit | The read-only Python query below | Android 86 owed; iOS 333 owed; all placed; both platform gates blocked |

```python
from pathlib import Path
from project_os_cockpit import acceptance
from project_os_cockpit.index import Index

docs = Path('../your-trainer/docs').resolve()
index = Index.build(docs)
for platform, release in [('android', 'REL-0017'), ('ios', '')]:
    walk = acceptance.walk_payload(docs, index, platform=platform, release=release)
    gate = acceptance.gate_payload(docs, index, platform=platform)
    print(platform, walk['counts'], gate['blocked'])
```

These are focused verification results. No full application suite, live hardware walk, store-console check, production deployment or comparative productivity study was performed.

## Maintenance

Keep these findings as a dated observation. Re-run the queries when the release scope or candidate revision changes. Add subsequent measurements with their date and revision rather than rewriting this observation as if it described the new state.
