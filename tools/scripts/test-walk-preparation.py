#!/usr/bin/env python3
"""Focused regression checks for declared walk preparation and survey nesting."""

import importlib.util
import pathlib
import sys
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("walk-sheet.py")
spec = importlib.util.spec_from_file_location("walk_sheet_preparation_test", MODULE_PATH)
walk = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = walk
spec.loader.exec_module(walk)


PROCEDURE = """---
type: "[[reference]]"
sitting: "The bench"
requires:
  2: [1]
  4: [2, 1]
step_platforms:
  3: [ios]
action_for:
  2:
    android: "Bind the power meter from the equipment panel."
    ios: "Bind the power meter from Settings, Equipment."
state_for:
  4: "The same ride is running with the meter connected."
capture_for:
  1: "Record the trainer's starting cadence."
use_capture:
  4: [1]
timer_for:
  4: 12
readiness_for:
  4: {kind: preparation, reason: "Bring the power meter to the bench.", issue: "ISS-1001", platforms: [android]}
setup_for:
  trainer: all
  meter: [2]
  phone: [3]
  finish: [4]
setup_platforms:
  phone: [ios]
---

# Procedure

## Setup

- [trainer] Connect the trainer.
- [meter] Place the meter nearby.
- [phone] Open the iPhone build.
- [finish] Keep the ride running.

## Steps

1. **Equipment panel (SUR-0001).** Connect the trainer.
2. **Equipment panel (SUR-0001).** Bind the power meter.
   - The meter appears. `TST-1001.1`
3. **Equipment panel (SUR-0001).** Read the iPhone source line.
   - The source line names the meter. `TST-1003.1`
4. **Ride cockpit (SUR-0002).** Check cadence.
   - The tile shows cadence. `TST-1002.1`
"""


class WalkPreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.docs = self.root / "docs"
        self.path = self.docs / "tests/acceptance/walk/the-bench.md"
        self.path.parent.mkdir(parents=True)
        self.path.write_text(PROCEDURE, encoding="utf-8")
        self.checks = {
            "TST-1001": walk.Check("TST-1001", "Meter", "meter.md", "Bench",
                                   steps="1. Bind meter.", expect="- The meter appears."),
            "TST-1002": walk.Check("TST-1002", "Cadence", "cadence.md", "Bench",
                                   steps="1. Read tile.", expect="- The tile shows cadence."),
            "TST-1003": walk.Check("TST-1003", "iPhone", "iphone.md", "Bench",
                                   steps="1. Read source.", expect="- The source line names the meter."),
        }
        self.sitting = walk.Sitting("The bench", checks=list(self.checks))

    def procedure(self):
        procedure, = walk.load_procedures(self.docs, self.root)
        walk.name_surfaces(procedure.steps, {
            "SUR-0001": walk.Surface("SUR-0001", "Equipment panel"),
            "SUR-0002": walk.Surface("SUR-0002", "Ride cockpit"),
        })
        return procedure

    def placed(self, platform, owed):
        procedure = self.procedure()
        entry = walk.Placed(self.sitting, [self.checks[item] for item in owed])
        walk.attach_procedure(entry, procedure, self.checks, set(owed), [self.sitting],
                              {}, platform=platform, known=self.checks)
        self.assertEqual([], procedure.problems)
        return entry

    def test_a_known_surface_id_names_the_screen_and_keeps_its_link(self):
        procedure = self.procedure()
        by_number = {step.number: step for step in procedure.steps}
        self.assertEqual("Equipment panel", by_number[1].surface_said)
        self.assertEqual("SUR-0001", by_number[1].surface_id)
        self.assertEqual("Ride cockpit", by_number[4].surface_said)
        self.assertEqual("SUR-0002", by_number[4].surface_id)

        # A missing surface note still leaves the authored id visible, so the
        # action does not silently lose its screen when a workspace is partial.
        walk.name_surfaces(procedure.steps, {})
        self.assertEqual("SUR-0001", by_number[1].surface_said)
        self.assertEqual("SUR-0001", by_number[1].surface_id)

    def test_transitive_actions_and_only_their_setup_survive(self):
        android = self.placed("android", ["TST-1002"])
        self.assertEqual([1, 2, 4], [step.number for step in android.steps])
        self.assertIn("Connect the trainer", android.setup)
        self.assertIn("Place the meter nearby", android.setup)
        self.assertIn("Keep the ride running", android.setup)
        self.assertNotIn("iPhone", android.setup)
        out = []
        walk.render_procedure(android, out)
        rendered = "\n".join(out)
        self.assertIn("Step 1", rendered)
        self.assertIn("preparation", rendered)
        self.assertNotIn("The meter appears.", rendered)
        self.assertIn("The tile shows cadence.", rendered)
        self.assertIn("**Required state:**", rendered)
        self.assertIn("The same ride is running with the meter connected.", rendered)
        self.assertIn("Bind the power meter from the equipment panel.", rendered)

    def test_ios_action_and_setup_appear_only_for_ios(self):
        ios = self.placed("ios", ["TST-1002", "TST-1003"])
        self.assertEqual([1, 2, 3, 4], [step.number for step in ios.steps])
        self.assertIn("Open the iPhone build", ios.setup)
        self.assertIn("Bind the power meter from Settings, Equipment.", ios.steps[1].head)
        self.assertEqual({}, ios.steps[-1].readiness)

    def test_state_declaration_survives_omission_and_respects_platform(self):
        def placed(platform):
            procedure = self.procedure()
            procedure.requires[4] = [1]
            procedure.steps[1].state_declared = "The meter is connected."
            procedure.steps[2].state_declared = "The iPhone scan is open."
            procedure.steps[3].state_declared = ""
            entry = walk.Placed(self.sitting, [self.checks["TST-1002"]])
            walk.attach_procedure(entry, procedure, self.checks, {"TST-1002"},
                                  [self.sitting], {}, platform=platform, known=self.checks)
            self.assertEqual([], procedure.problems)
            return entry

        android = placed("android")
        self.assertEqual([1, 4], [step.number for step in android.steps])
        self.assertEqual("The meter is connected.", android.steps[-1].required_state)
        ios = placed("ios")
        self.assertEqual([1, 4], [step.number for step in ios.steps])
        self.assertEqual("The iPhone scan is open.", ios.steps[-1].required_state)

    def test_capture_and_timer_are_authored_and_only_requested_when_used(self):
        cadence = self.placed("android", ["TST-1002"])
        self.assertTrue(cadence.steps[0].capture_needed)
        self.assertEqual([1], cadence.steps[-1].uses_capture)
        self.assertEqual(12, cadence.steps[-1].timer_seconds)
        out = []
        walk.render_procedure(cadence, out)
        rendered = "\n".join(out)
        self.assertIn("Capture here for a later comparison", rendered)
        self.assertIn("**Optional timer:** 12 seconds", rendered)
        self.assertIn("Compare with evidence from source step 1", rendered)
        self.assertIn("**Needs preparation:** Bring the power meter to the bench. (ISS-1001)", rendered)
        meter = self.placed("android", ["TST-1001"])
        self.assertFalse(meter.steps[0].capture_needed)
        out = []
        walk.render_procedure(meter, out)
        self.assertNotIn("Capture here for a later comparison", "\n".join(out))

    def test_capture_source_must_be_declared_and_required(self):
        procedure = self.procedure()
        procedure.requires[4] = [2]
        problems = walk.validate_preparation(procedure, "android")
        self.assertTrue(any("must require evidence source step 1" in problem
                            for problem in problems))

    def test_broken_declarations_are_refused(self):
        procedure = self.procedure()
        procedure.requires = {2: [1], 4: [5, 1], 1: [4]}
        procedure.setup_items[0].steps.add(8)
        problems = walk.validate_preparation(procedure, "android")
        self.assertTrue(any("absent step 5" in problem for problem in problems))
        self.assertTrue(any("cycle" in problem for problem in problems))
        self.assertTrue(any("setup item trainer names absent step 8" in problem
                            for problem in problems))
        entry = walk.Placed(self.sitting, [self.checks["TST-1002"]])
        walk.attach_procedure(entry, procedure, self.checks, {"TST-1002"},
                              [self.sitting], {}, platform="android", known=self.checks)
        self.assertTrue(procedure.problems)
        self.assertEqual([], entry.steps)
        sheet = walk.Walk("REL-0001", "android", "2026-09-16", [], [entry], [])
        rendered = walk.render(sheet)
        self.assertIn("no longer matches what the release owes", rendered)
        self.assertIn("TST-1002", rendered)

    def test_cross_platform_prerequisite_is_refused(self):
        procedure = self.procedure()
        procedure.requires[4] = [3]
        problems = walk.validate_preparation(procedure, "android")
        self.assertTrue(any("unavailable on android" in problem for problem in problems))

    def test_malformed_tag_beside_valid_coverage_keeps_the_fallback(self):
        self.path.write_text(
            PROCEDURE.replace("The meter appears. `TST-1001.1`",
                              "The meter appears. `TST-1001.1` `TST-1001.1a`"),
            encoding="utf-8")
        procedure = self.procedure()
        entry = walk.Placed(self.sitting, [self.checks["TST-1001"]])
        walk.attach_procedure(entry, procedure, self.checks, {"TST-1001"},
                              [self.sitting], {}, platform="android", known=self.checks)
        self.assertTrue(any("malformed expectation tag `TST-1001.1a`" in problem
                            for problem in procedure.problems))
        self.assertEqual([], entry.steps)
        sheet = walk.Walk("REL-0001", "android", "2026-09-16", [], [entry], [])
        rendered = walk.render(sheet)
        self.assertIn("no longer matches what the release owes", rendered)
        self.assertIn("TST-1001", rendered)
        self.assertIn("The meter appears.", rendered)

    def test_changed_child_stays_under_its_unchanged_parent(self):
        surfaces = {
            "SUR-0001": walk.Surface("SUR-0001", "Equipment panel"),
            "SUR-0002": walk.Surface("SUR-0002", "Cadence scanner", "SUR-0001"),
        }
        change = walk.Change("CHG-1", "Cadence scan", "change.md",
                             screens=[("SUR-0002", "The scanner names its target.")])
        survey = walk.build_survey([change], surfaces)
        self.assertEqual(["SUR-0001", "SUR-0002"], [screen.id for screen in survey])
        self.assertEqual([], survey[0].sentences)
        self.assertEqual("SUR-0001", survey[1].parent)

    def test_unscripted_check_readiness_is_platform_specific(self):
        declared, problems = walk.parse_check_readiness({
            "ios": {"kind": "decision", "reason": "Choose the iOS scope.",
                    "issue": "ISS-1001"},
        }, "check.md")
        self.assertEqual([], problems)
        check = walk.Check("TST-1004", "Android backup", "check.md", "Bench",
                           readiness_for=declared)
        ios = []
        android = []
        walk.render_check(check, ios, "ios")
        walk.render_check(check, android, "android")
        self.assertIn("**Needs a decision:** Choose the iOS scope.", "\n".join(ios))
        self.assertIn("Related issue: ISS-1001.", "\n".join(ios))
        self.assertNotIn("Needs a decision", "\n".join(android))

    def test_malformed_unscripted_check_readiness_is_reported(self):
        declared, problems = walk.parse_check_readiness({
            "ios": {"kind": "decision", "reason": "  "},
            "iOS": {"kind": "preparation", "reason": "Find the device."},
        }, "check.md")
        self.assertEqual({}, declared)
        self.assertEqual(2, len(problems))
        self.assertTrue(all("walk_readiness_for" in problem for problem in problems))
        check = walk.Check("TST-1004", "Bad readiness", "check.md", "Bench",
                           readiness_for=declared, readiness_problems=problems)
        self.assertEqual("decision", walk.check_readiness(check, "ios")["kind"])
        rendered = []
        walk.render_check(check, rendered, "ios")
        self.assertIn("Needs a decision", "\n".join(rendered))


if __name__ == "__main__":
    unittest.main()
