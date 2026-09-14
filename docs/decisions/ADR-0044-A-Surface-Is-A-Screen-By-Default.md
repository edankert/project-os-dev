---
type: "[[adr]]"
id: ADR-0044
aliases: ["ADR-0044"]
title: "A surface is a screen by default: a state is not a surface, a dialog is a child, a check that crosses screens takes the parent, and one screen stays one surface on every platform"
status: accepted
decided_option: "3"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
decided: 2026-09-14
source: ["Edwin, 2026-09-14, approving the goal: 'It opens with the app screens this release changed: what each one now shows, with before and after screenshots.'", "Edwin, 2026-09-14: no new 'screens' concept; update the surfaces to be the real screens", "Review of your-trainer's 16 SUR-* notes and its REL-0017 walk sheet, 2026-09-14"]
decision: "Option 3, accepted by Edwin 2026-09-14. A SUR-* note names a screen unless it says otherwise. TAXONOMY.md gains four rules: a state such as data-only or pacer on is not a surface; a dialog, sheet or panel is a child surface with parent:; a check that walks several screens names their parent screen; a screen placed differently on each platform stays one surface. subsystem and surface-less stay as exceptions for checks with no screen. The 12-15 surface target from project-os-cockpit FEAT-0130 applies to top-level screens only. A surface note carries its screenshot keys as a gallery: list of key or key:state entries."
context: "The template already says a surface is 'a place in the product' with kind and parent:, but the first large corpus built its surfaces by merging test categories. The survey therefore names categories such as Hardware, which spans five screens, and never the screen a person opens."
alternatives: ["Keep surfaces as test categories", "Add a separate screen type beside surfaces"]
consequences: ["Consumer repos rewrite area: on every acceptance check once, after an approved mapping", "The number of surfaces rises; a person holds the top-level screens in their head and the children sit under them", "A gallery key maps to a surface plus an optional state, so screenshots and surfaces share one vocabulary", "project-os-cockpit groups ~checks by screen, parents first"]
supersedes: ""
superseded: ""
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]"]
---

# A surface is a screen by default

## Context

A person checking a release opens screens. The walk sheet's survey should therefore list screens. Today it cannot, because the surfaces in the largest consumer are test categories.

`tools/instructions/TAXONOMY.md`, "`kind` (surfaces)", already defines a surface as "a place in the product" and gives it a `kind` (screen, flow, subsystem, surface-less) and an optional `parent:`. So the type is right. What went wrong is how the first corpus used it.

your-trainer built its 16 `SUR-*` notes on 2026-08-20 by merging 94 hand-typed `area:` strings into categories (its TASK-0515, done in project-os-cockpit FEAT-0130). Five of the notes say `kind: screen` and are not screens. "Riding — routes", "Riding — simulation" and "Riding — structured" are all the same ride cockpit in different modes. "App shell & UX" is not a place anyone navigates to. "Hardware" holds 70 checks spread over the equipment panel, the device scanner, Bluetooth diagnostics, the trainer compatibility test and protocol behaviour with no screen at all.

Meanwhile that repo already has a real screen vocabulary in three places: the parity gallery's capture keys (`equipment-hub`, `equipment-hub-dataonly`, `cockpit-hrzone-dataonly`, `trainer-test`, `developer`), `docs/GLOSSARY.md`'s canonical locations, and the Android `*Screen.kt`, `*Dialog.kt` and `*Sheet.kt` files.

Edwin said on 2026-09-14 that he does not want a new "screens" concept beside surfaces. The surfaces should become the real screens.

## Options

1. **Keep surfaces as test categories.** Costs nothing now. The survey keeps naming "Hardware" and a person keeps translating it into the five screens it might mean.
2. **Add a separate screen type beside surfaces.** Buys a clean vocabulary without touching existing checks. Costs a second grouping on every check, a second set of notes, and the question of which one a survey uses. Edwin rejected it.
3. **A surface is a screen by default, with four rules for the hard cases.** Uses the type and fields that already exist. Costs a one-time rewrite of `area:` in each consumer, after a mapping the owner approves.

## Decision

**Option 3, accepted 2026-09-14.** A `SUR-*` note names a screen unless its `kind` says otherwise. `TAXONOMY.md` gains these rules, stated there once:

1. **A state is not a surface.** Data-only mode, the pacer switched on, or a FREE tier are states of a screen. The screen is the surface. Where a screenshot tool captures a state separately, its key maps to the surface plus the state, for example `equipment-hub-dataonly` maps to the equipment panel in the data-only state.
2. **A dialog, sheet or panel is a child surface.** It gets its own `SUR-*` note with `parent:` naming the screen it opens from. A check about the dialog names the dialog.
3. **A check that walks several screens names their parent screen.** Where the screens share no parent, the check names the screen it starts on.
4. **A screen placed differently per platform stays one surface.** The equipment panel sits on the Workouts screen on Android and in an Equipment Hub on iOS. It is one surface, and the note's "What it is" says where each platform puts it.

`subsystem` and `surface-less` stay, as the exceptions for checks with no screen (sync, physics, the build).

Two more points, decided with the rules:

- **The 12 to 15 surface target from project-os-cockpit FEAT-0130 applies to top-level screens only.** Children (dialogs, sheets, panels, sections) sit below them and do not count toward it.
- **A surface note lists its screenshot keys** in a `gallery:` field. Each entry is a `key`, or `key:state` when the key captures the screen in a state, for example `gallery: [equipment-hub, "equipment-hub-dataonly:data-only"]`.

## Alternatives

- Option 1, keep the categories. Rejected because the survey cannot name what a person opens.
- Option 2, a separate screen type. Rejected by the owner, and because two groupings on one check disagree the first time someone edits one.

## Consequences

- Each consumer rewrites `area:` on its acceptance checks once, retired checks included, after the owner approves a mapping table. your-trainer's mapping is its TASK-0900 and it pauses for Edwin.
- There will be more surface notes than the 12 to 15 project-os-cockpit FEAT-0130 aimed for. That target now applies to top-level screens only; children sit under them.
- `area:` still holds the surface title string. project-os-cockpit ISS-0250 (renaming a surface orphans its checks) applies to every rename this causes, so a consumer renames surfaces and checks in one commit.
- The cockpit's `~checks` page groups by screen with children under parents, following these rules (project-os-cockpit FEAT-0150).

## Acceptance

- [ ] **The four rules are in TASK-0116's TAXONOMY.md text and nowhere else.**
- [x] **Where the gallery-key-to-surface mapping lives is decided.** On the surface note, as a `gallery:` list of `key` or `key:state` entries. Decided by Edwin 2026-09-14 (Decision record below). Reason: the surface note is where a screen is described once, so its pictures belong there too, and no second file can drift from it.

## Decision record

> [!note] Accept — 2026-09-14 (user:edwin)
> "v2.2.0 should wait. go with your recommendations for the others, will I start the project-os-dev and cockpit phase first?"
> Recorded as: Option 3 accepted. The 12 to 15 surface target applies to top-level screens only, with children below. The gallery-key map lives on the surface note as a `gallery:` list of `key` or `key:state` entries.
