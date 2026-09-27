#!/usr/bin/env python3
"""Focused regression checks for declared release test preparation and what-changed nesting."""

import sys as _sys
# No bytecode, ever: a cached compile Python judges current is used in place of
# the source, and one from 14 September made a passing check report failures on
# 2026-09-20 (project-os-dev ISS-0073). Writing none means none can go stale.
_sys.dont_write_bytecode = True


import importlib.util
import pathlib
import sys
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("release-test.py")
spec = importlib.util.spec_from_file_location("release_test_preparation_test", MODULE_PATH)
rt = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rt
spec.loader.exec_module(rt)
#: These fixtures quote expected lines in the older form, and what they test is
#: preparation, not quoting, so a quote is a warning here as `quoted_lines:
#: warning` makes it in a repo (project-os-dev REQ-0034).
rt.QUOTED_EXPECTATIONS_REFUSED = False


PROCEDURE = """---
type: "[[reference]]"
section: "The bench"
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


class ReleaseTestPreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.docs = self.root / "docs"
        self.path = self.docs / "tests/acceptance/release-test/the-bench.md"
        self.path.parent.mkdir(parents=True)
        self.path.write_text(PROCEDURE, encoding="utf-8")
        self.checks = {
            "TST-1001": rt.Check("TST-1001", "Meter", "meter.md", "Bench",
                                   steps="1. Bind meter.", expect="- The meter appears."),
            "TST-1002": rt.Check("TST-1002", "Cadence", "cadence.md", "Bench",
                                   steps="1. Read tile.", expect="- The tile shows cadence."),
            "TST-1003": rt.Check("TST-1003", "iPhone", "iphone.md", "Bench",
                                   steps="1. Read source.", expect="- The source line names the meter."),
        }
        self.section = rt.Section("The bench", checks=list(self.checks))

    def procedure(self):
        procedure, = rt.load_procedures(self.docs, self.root)
        rt.name_surfaces(procedure.steps, {
            "SUR-0001": rt.Surface("SUR-0001", "Equipment panel"),
            "SUR-0002": rt.Surface("SUR-0002", "Ride cockpit"),
        })
        return procedure

    def placed(self, platform, owed):
        procedure = self.procedure()
        entry = rt.Placed(self.section, [self.checks[item] for item in owed])
        rt.attach_procedure(entry, procedure, self.checks, set(owed), [self.section],
                              {}, platform=platform, known=self.checks)
        self.assertEqual([], procedure.problems)
        return entry

    def page_of(self, entry, platform):
        """The section as the page prints it, from the same model as --json."""
        sheet = rt.ReleaseTest("REL-0001", platform, "2026-09-27", [], [entry], [])
        section = rt.payload(sheet)["sections"][0]
        out = []
        rt.render_section(section, platform, out)
        return section, "\n".join(out)

    def test_a_known_surface_id_names_the_screen_and_keeps_its_link(self):
        procedure = self.procedure()
        by_number = {step.number: step for step in procedure.steps}
        self.assertEqual("Equipment panel", by_number[1].surface_said)
        self.assertEqual("SUR-0001", by_number[1].surface_id)
        self.assertEqual("Ride cockpit", by_number[4].surface_said)
        self.assertEqual("SUR-0002", by_number[4].surface_id)

        # A missing surface note still leaves the authored id visible, so the
        # action does not silently lose its screen when a workspace is partial.
        rt.name_surfaces(procedure.steps, {})
        self.assertEqual("SUR-0001", by_number[1].surface_said)
        self.assertEqual("SUR-0001", by_number[1].surface_id)

    def test_transitive_actions_and_only_their_setup_survive(self):
        android = self.placed("android", ["TST-1002"])
        self.assertEqual([1, 2, 4], [step.number for step in android.steps])
        self.assertIn("Connect the trainer", android.setup)
        self.assertIn("Place the meter nearby", android.setup)
        self.assertIn("Keep the ride running", android.setup)
        self.assertNotIn("iPhone", android.setup)
        section, rendered = self.page_of(android, "android")
        checks = [c for g in section["groups"] for c in g["checks"]]
        self.assertEqual([1, 2, 3], [c["number"] for c in checks])
        self.assertEqual([True, True, False], [c["preparation"] for c in checks])
        self.assertIn("- [ ] **1.** ", rendered)
        self.assertIn("Preparation for a later check. Nothing to record.", rendered)
        self.assertNotIn("The meter appears.", rendered)
        self.assertIn("The tile shows cadence.", rendered)
        self.assertIn("Start: The same ride is running with the meter connected.", rendered)
        self.assertIn("Bind the power meter from the equipment panel.", rendered)

    def test_setup_for_an_omitted_step_is_left_out(self):
        # Mutation check, 2026-09-24 (TASK-0125): printing every setup item
        # passed every other test, because the one negative assertion above is
        # met by the platform filter. `finish` is scoped to step 4, which a release test
        # owing only TST-1001 (step 2, needing step 1) leaves out.
        android = self.placed("android", ["TST-1001"])
        self.assertEqual([1, 2], [step.number for step in android.steps])
        self.assertIn("Connect the trainer", android.setup)
        self.assertIn("Place the meter nearby", android.setup)
        self.assertNotIn("Keep the ride running", android.setup)

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
            entry = rt.Placed(self.section, [self.checks["TST-1002"]])
            rt.attach_procedure(entry, procedure, self.checks, {"TST-1002"},
                                  [self.section], {}, platform=platform, known=self.checks)
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
        _section, rendered = self.page_of(cadence, "android")
        self.assertIn("_Keep what you see: ", rendered)
        self.assertIn(" ⏱ 12 s", rendered)
        # Step 4 of the procedure prints as check 3, and the line naming the
        # step it compares with uses the printed number (ISS-0086).
        self.assertIn("Compare with what you kept at check 1.", rendered)
        self.assertIn("Bring the power meter to the bench. (ISS-1001) Suggested: Blocked.", rendered)
        meter = self.placed("android", ["TST-1001"])
        self.assertFalse(meter.steps[0].capture_needed)
        _section, rendered = self.page_of(meter, "android")
        self.assertNotIn("Keep what you see", rendered)

    def test_capture_source_must_be_declared_and_required(self):
        procedure = self.procedure()
        procedure.requires[4] = [2]
        problems = rt.validate_preparation(procedure, "android")
        self.assertTrue(any("must require evidence source step 1" in problem
                            for problem in problems))

    def test_broken_declarations_are_refused(self):
        procedure = self.procedure()
        procedure.requires = {2: [1], 4: [5, 1], 1: [4]}
        procedure.setup_items[0].steps.add(8)
        problems = rt.validate_preparation(procedure, "android")
        self.assertTrue(any("absent step 5" in problem for problem in problems))
        self.assertTrue(any("cycle" in problem for problem in problems))
        self.assertTrue(any("setup item trainer names absent step 8" in problem
                            for problem in problems))
        entry = rt.Placed(self.section, [self.checks["TST-1002"]])
        rt.attach_procedure(entry, procedure, self.checks, {"TST-1002"},
                              [self.section], {}, platform="android", known=self.checks)
        self.assertTrue(procedure.problems)
        self.assertEqual([], entry.steps)
        sheet = rt.ReleaseTest("REL-0001", "android", "2026-09-16", [], [entry], [])
        rendered = rt.render(sheet)
        self.assertIn("no longer matches what the release owes", rendered)
        self.assertIn("TST-1002", rendered)

    def test_two_instructions_for_one_step_are_refused(self):
        # TASK-0125: the parser keeps the last of two values for one key, so
        # the first instruction vanished without a word.
        self.path.write_text(PROCEDURE.replace(
            'state_for:\n  4: "The same ride is running with the meter connected."',
            'state_for:\n  4: "Signed in as FREE."\n  4: "Signed in as PRO."'), encoding="utf-8")
        problems = rt.validate_preparation(self.procedure(), "android")
        self.assertTrue(any("`state_for` declares 4 twice" in problem for problem in problems))
        self.path.write_text(PROCEDURE.replace(
            "step_platforms:\n  3: [ios]", "step_platforms: {3: [ios], 3: [android]}"), encoding="utf-8")
        problems = rt.validate_preparation(self.procedure(), "android")
        self.assertTrue(any("`step_platforms` declares 3 twice" in problem for problem in problems))
        self.path.write_text(PROCEDURE, encoding="utf-8")
        self.assertEqual([], [problem for problem in rt.validate_preparation(self.procedure(), "android")
                              if "twice" in problem])

    def test_a_declaration_that_can_never_apply_is_refused(self):
        procedure = self.procedure()
        phone = next(item for item in procedure.setup_items if item.id == "phone")
        phone.platforms = {"android"}
        procedure.steps[1].platforms = {"android"}
        procedure.steps[3].platforms = {"ios"}
        problems = rt.validate_preparation(procedure, "")
        self.assertTrue(any("setup item phone is limited to android, but none of its steps runs there"
                            in problem for problem in problems))
        self.assertTrue(any("step 2 has an `action_for` variant for ios" in problem for problem in problems))
        self.assertTrue(any("step 4's `readiness_for` is limited to android" in problem for problem in problems))
        self.assertFalse(any("can never" in problem or "none of its steps" in problem
                             for problem in rt.validate_preparation(self.procedure(), "")))

    def test_a_platform_the_repo_has_no_ledger_for_is_refused(self):
        ledgers = self.docs / rt.LEDGERS_REL
        ledgers.mkdir(parents=True)
        for name in ("WORKING-android", "WORKING-ios"):
            (ledgers / (name + ".json")).write_text("{}", encoding="utf-8")
        self.assertEqual([], [problem for problem in self.procedure().parse_problems if "names platform" in problem])
        self.path.write_text(PROCEDURE.replace("  3: [ios]", "  3: [andriod]"), encoding="utf-8")
        problems = rt.validate_preparation(self.procedure(), "android")
        self.assertTrue(any("`step_platforms` names platform andriod, and this repo keeps ledgers only for android, ios"
                            in problem for problem in problems))

    def test_prerequisites_are_followed_through_a_chain(self):
        # FEAT-0033 review, 2026-09-24: the fixture's `4: [2, 1]` names step 1
        # directly, so a closure that stopped after one hop passed every test.
        self.path.write_text(PROCEDURE.replace("  4: [2, 1]", "  4: [2]")
                             .replace("use_capture:\n  4: [1]\n", ""), encoding="utf-8")
        android = self.placed("android", ["TST-1002"])
        self.assertEqual([1, 2, 4], [step.number for step in android.steps])

    def test_a_later_step_cannot_be_a_prerequisite(self):
        procedure = self.procedure()
        procedure.requires[2] = [3]
        problems = rt.validate_preparation(procedure, "")
        self.assertTrue(any("step 2 requires step 3, but a prerequisite must come earlier" in problem
                            for problem in problems))

    def test_frontmatter_ends_at_its_own_delimiter(self):
        # A `---` inside a frontmatter string must not cut the text short.
        self.path.write_text(PROCEDURE.replace(
            'state_for:\n  4: "The same ride is running with the meter connected."',
            'state_for:\n  4: "Ride --- then stop."\n  4: "Signed in as PRO."'), encoding="utf-8")
        problems = rt.validate_preparation(self.procedure(), "android")
        self.assertTrue(any("`state_for` declares 4 twice" in problem for problem in problems))

    def test_the_numbering_remark_counts_only_this_platforms_steps(self):
        # FEAT-0033 review round 2: the remark listed every step's written
        # number but was raised from the platform's steps; nothing held it.
        self.path.write_text(PROCEDURE.replace("\n3. **Equipment", "\n7. **Equipment")
                             .replace("\n4. **Ride", "\n9. **Ride"), encoding="utf-8")
        entry = self.placed("android", ["TST-1002"])
        remark = next(r for r in entry.procedure.remarks if "numbers its steps" in r)
        self.assertIn("numbers its steps 1, 2, 9", remark)
        self.assertIn("prints them 1 to 3", remark)

    def test_printed_numbers_run_from_one_and_setup_names_them(self):
        # REQ-0033 closes ISS-0086 the other way from its 2026-09-25 option 1:
        # the page numbers the checks it prints from 1, and every line it
        # writes about a check uses that number. Steps 1, 2 and 4 of the
        # procedure print as checks 1, 2 and 3.
        android = self.placed("android", ["TST-1002"])
        section, rendered = self.page_of(android, "android")
        numbers = [line.split("**")[1] for line in rendered.splitlines() if line.startswith("- [ ] **")]
        self.assertEqual(["1.", "2.", "3."], numbers)
        self.assertNotIn("Step 4", rendered)
        # Setup splits three ways: `all` is done before starting, and an item
        # tied to later steps names the printed check that needs it.
        self.assertEqual(["Connect the trainer."], section["setup"]["before"])
        self.assertEqual([{"check": 2, "text": "Place the meter nearby."},
                          {"check": 3, "text": "Keep the ride running."}],
                         section["setup"]["later"])
        self.assertIn("- Check 2 needs: Place the meter nearby.", rendered)
        self.assertIn("1. Connect the trainer.", rendered)

    def test_a_comparison_names_the_printed_number_of_its_source(self):
        # Step 1 is left out, so procedure steps 2 and 3 print as checks 1 and
        # 2, and the comparison at step 3 names check 1, not step 2.
        self.path.write_text('''---
type: "[[reference]]"
section: "The bench"
requires:
  3: [2]
capture_for:
  2: "Record the cadence."
use_capture:
  3: [2]
---

# Procedure

## Setup

Connect the trainer.

## Steps

1. Read the panel.
   - `TST-1001.1`
2. Record the cadence.
3. Check cadence again.
   - `TST-1002.1`
''', encoding="utf-8")
        entry = self.placed("android", ["TST-1002"])
        section, rendered = self.page_of(entry, "android")
        checks = [c for g in section["groups"] for c in g["checks"]]
        self.assertEqual([1, 2], [c["number"] for c in checks])
        self.assertEqual([1], checks[1]["compare_with"])
        self.assertIn("Compare with what you kept at check 1.", rendered)

    def test_a_section_budget_counts_printed_checks_not_test_notes(self):
        # One owed test note, three printed checks (two of them preparation).
        entry = self.placed("android", ["TST-1002"])
        sheet = rt.ReleaseTest("REL-0001", "android", "2026-09-27", [], [entry], [])
        found = rt.length_findings(rt.payload(sheet),
                                   rt.LengthLimits(section_base=1, section_per_check=1))
        self.assertTrue(any("over its budget of 4 (1 + 1 for each of its 3 checks)" in f
                            for f in found), found)

    def test_printed_words_count_what_the_tester_reads(self):
        self.assertEqual(3, rt.printed_words("Open the panel. `TST-0401.1` `TST-0402`"))
        self.assertEqual(3, rt.printed_words("[The check](docs/tests/TST-1.md) **1.**"))
        self.assertEqual(0, rt.printed_words("![equipment-hub, now](docs/a.png)"))
        self.assertEqual(3, rt.printed_words("#### Hub layout\n- [ ] two"))

    def test_an_expected_line_loses_the_checks_own_step_number(self):
        self.assertEqual("The tile shows cadence.",
                         rt.shown_expected("- Step 3: The tile shows cadence. `TST-1002.3`"))
        self.assertEqual("**The tile shows cadence.**",
                         rt.shown_expected("**Step 3: The tile shows cadence.**"))
        self.assertEqual("**The tile** shows cadence.",
                         rt.shown_expected("Step 3: **the tile** shows cadence."))
        self.assertEqual("The slot reads the trainer.",
                         rt.shown_expected("Step 1: the slot reads the trainer."))
        self.assertEqual("**The slot** reads the trainer.",
                         rt.shown_expected("Step 1: **the slot** reads the trainer."))
        self.assertEqual("`unknown` is shown.",
                         rt.shown_expected("Step 1: `unknown` is shown."))
        self.assertEqual("A step 3 of the ride is shown.",
                         rt.shown_expected("A step 3 of the ride is shown."))

    def test_a_step_prefix_in_single_emphasis_is_stripped(self):
        # Independent review, 2026-09-27: only `**` and `__` were stripped.
        self.assertEqual("Done.", rt.shown_expected("- *Step 2:* done."))
        self.assertEqual("Done.", rt.shown_expected("_Step 2:_ done."))
        self.assertEqual("*The tile shows cadence.*",
                         rt.shown_expected("*Step 3: the tile shows cadence.*"))
        self.assertEqual("_The tile_ shows cadence.",
                         rt.shown_expected("Step 3: _the tile_ shows cadence."))
        self.assertEqual("***The panel** shows.*",
                         rt.shown_expected("*Step 2: **the panel** shows.*"))

    def test_identical_expect_lines_keep_their_positions(self):
        # Independent review, 2026-09-27: a repeated line was dropped, so tag
        # .3 named line 4.
        check = rt.Check("TST-1009", "Twice", "c.md", "Bench",
                         steps="1. A.\n2. B.\n3. C.\n4. D.",
                         expect="- The slot is empty.\n- It connects.\n- The slot is empty.\n- It stays.")
        self.assertEqual(["The slot is empty."], rt.expect_for(check, "3"))
        self.assertEqual(["It stays."], rt.expect_for(check, "4"))
        unpaired = rt.Check("TST-1010", "Unpaired", "c.md", "Bench", steps="1. A.",
                            expect="- The slot is empty.\n- The slot is empty.\n- It stays.")
        self.assertEqual(["The slot is empty.", "It stays."], rt.expect_for(unpaired, "1"))

    def test_short_lines_with_no_release_tag_say_why_they_are_unused(self):
        short = rt.ShortLines("docs/what-changed-android.md", "v1",
                              {("CHG-1", "SUR-0001"): "A slot."})
        lines, why = rt.short_lines_for(short, "")
        self.assertEqual({}, lines)
        self.assertIn("no release has been tagged on this platform yet", why)
        self.assertIn("Impact sentences", why)
        change = rt.Change("CHG-1", "Slot", "change.md", screens=[("SUR-0001", "A slot.")])
        sheet = rt.build_release_test({}, [], [], release="R", platform="android",
                                      changes=[change], short_lines=short)
        self.assertIn("no release has been tagged", rt.render(sheet))

    def test_a_short_line_prints_once_for_two_impact_lines_on_one_screen(self):
        surfaces = {"SUR-0001": rt.Surface("SUR-0001", "Equipment panel")}
        change = rt.Change("CHG-1", "Slot", "change.md",
                           screens=[("SUR-0001", "A slot."), ("SUR-0001", "A label.")])
        short = {("CHG-1", "SUR-0001"): "The panel gains a slot."}
        screen, = rt.build_what_changed([change], surfaces, short=short)
        self.assertEqual([("CHG-1", "Slot", "The panel gains a slot.")], screen.sentences)
        self.assertEqual([True], screen.short)
        screen, = rt.build_what_changed([change], surfaces)
        self.assertEqual(["A slot.", "A label."], [s[2] for s in screen.sentences])

    def test_what_changed_names_the_platform_as_a_sentence_writes_it(self):
        for name, shown in (("android", "Android"), ("ios", "iOS"), ("macos", "macOS"),
                            ("testbed", "Testbed")):
            sheet = rt.build_release_test({}, [], [], release="R", platform=name,
                                          what_changed_tag="v1")
            self.assertIn("\n## What changed on %s\n" % shown, rt.render(sheet))

    def test_a_readiness_problem_offers_a_result_by_its_kind(self):
        self.assertEqual("blocked", rt._readiness({"kind": "preparation", "reason": "r"})["result"])
        self.assertEqual("question", rt._readiness({"kind": "decision", "reason": "r"})["result"])
        self.assertEqual("excused", rt._readiness({"kind": "preparation", "reason": "r",
                                                   "result": "excused"})["result"])
        self.assertEqual("Nobody owns one. Suggested: Excused.",
                         rt.readiness_line({"reason": "Nobody owns one.", "issue": "",
                                            "result": "excused"}))

    def test_cross_platform_prerequisite_is_refused(self):
        procedure = self.procedure()
        procedure.requires[4] = [3]
        problems = rt.validate_preparation(procedure, "android")
        self.assertTrue(any("unavailable on android" in problem for problem in problems))

    def test_malformed_tag_beside_valid_coverage_keeps_the_fallback(self):
        self.path.write_text(
            PROCEDURE.replace("The meter appears. `TST-1001.1`",
                              "The meter appears. `TST-1001.1` `TST-1001.1a`"),
            encoding="utf-8")
        procedure = self.procedure()
        entry = rt.Placed(self.section, [self.checks["TST-1001"]])
        rt.attach_procedure(entry, procedure, self.checks, {"TST-1001"},
                              [self.section], {}, platform="android", known=self.checks)
        self.assertTrue(any("malformed expectation tag `TST-1001.1a`" in problem
                            for problem in procedure.problems))
        self.assertEqual([], entry.steps)
        sheet = rt.ReleaseTest("REL-0001", "android", "2026-09-16", [], [entry], [])
        rendered = rt.render(sheet)
        self.assertIn("no longer matches what the release owes", rendered)
        self.assertIn("TST-1001", rendered)
        self.assertIn("The meter appears.", rendered)

    def test_changed_child_stays_under_its_unchanged_parent(self):
        surfaces = {
            "SUR-0001": rt.Surface("SUR-0001", "Equipment panel"),
            "SUR-0002": rt.Surface("SUR-0002", "Cadence scanner", "SUR-0001"),
        }
        change = rt.Change("CHG-1", "Cadence scan", "change.md",
                             screens=[("SUR-0002", "The scanner names its target.")])
        changed = rt.build_what_changed([change], surfaces)
        self.assertEqual(["SUR-0001", "SUR-0002"], [screen.id for screen in changed])
        self.assertEqual([], changed[0].sentences)
        self.assertEqual("SUR-0001", changed[1].parent)

    def test_a_section_tests_the_screens_of_the_checks_it_names(self):
        # REQ-0035: a bench section claims its checks by id and names no
        # surface; its checks' screens are still the ones it tests, and the
        # first section in order keeps a screen.
        surfaces = {
            "SUR-0001": rt.Surface("SUR-0001", "Equipment panel"),
            "SUR-0002": rt.Surface("SUR-0002", "Cadence scanner", "SUR-0001"),
            "SUR-0003": rt.Surface("SUR-0003", "Ride cockpit"),
        }
        by_title = {s.title: s.id for s in surfaces.values()}
        checks = {"TST-1001": rt.Check("TST-1001", "Hub", "c.md", "Equipment panel")}
        sections = [rt.Section("The bench", checks=["TST-1001"]),
                    rt.Section("Compatibility", surfaces=["Equipment panel", "Ride cockpit"])]
        homes = rt.screen_homes(sections, surfaces, by_title, checks)
        self.assertEqual("The bench", homes["SUR-0001"])
        self.assertEqual("The bench", homes["SUR-0002"])
        self.assertEqual("Compatibility", homes["SUR-0003"])

    def test_a_changed_screen_whose_section_prints_nothing_is_on_the_overview(self):
        surfaces = {"SUR-0001": rt.Surface("SUR-0001", "Equipment panel"),
                    "SUR-0003": rt.Surface("SUR-0003", "Ride cockpit")}
        by_title = {s.title: s.id for s in surfaces.values()}
        checks = {"TST-1001": rt.Check("TST-1001", "Hub", "c.md", "Equipment panel")}
        sections = [rt.Section("Panel", surfaces=["Equipment panel"]),
                    rt.Section("Rides", surfaces=["Ride cockpit"])]
        change = rt.Change("CHG-1", "Both", "change.md",
                           screens=[("SUR-0001", "A slot."), ("SUR-0003", "A lap.")])
        sheet = rt.build_release_test(checks, [], sections, release="REL-1",
                                      platform="android", surfaces=by_title,
                                      surface_notes=surfaces, changes=[change],
                                      what_changed_tag="v1")
        self.assertEqual(["SUR-0001"], [s.id for s in sheet.sections[0].what_changed])
        self.assertEqual(["SUR-0003"], [s.id for s in sheet.what_changed_overview])
        rendered = rt.render(sheet)
        self.assertIn("No section on this sheet tests these changed screens", rendered)

    def test_a_section_with_no_changed_screen_says_so(self):
        surfaces = {"SUR-0001": rt.Surface("SUR-0001", "Equipment panel")}
        checks = {"TST-1001": rt.Check("TST-1001", "Hub", "c.md", "Equipment panel")}
        sheet = rt.build_release_test(checks, [], [rt.Section("Panel", surfaces=["Equipment panel"])],
                                      release="REL-1", platform="android",
                                      surfaces={"Equipment panel": "SUR-0001"},
                                      surface_notes=surfaces, changes=[],
                                      what_changed_tag="v1")
        self.assertIn("Nothing changed on the screens this section tests.", rt.render(sheet))

    def test_an_undeclared_change_is_named_only_with_more_than_one_platform(self):
        change = rt.Change("CHG-1", "Slot", "change.md", screens=[("SUR-0001", "A slot.")])
        one = rt.build_release_test({}, [], [], release="R", platform="android",
                                    changes=[change], known_platforms=["android"])
        two = rt.build_release_test({}, [], [], release="R", platform="android",
                                    changes=[change], known_platforms=["android", "ios"])
        self.assertEqual([], one.undeclared)
        self.assertEqual(["CHG-1"], two.undeclared)

    def test_unscripted_check_readiness_is_platform_specific(self):
        declared, problems = rt.parse_check_readiness({
            "ios": {"kind": "decision", "reason": "Choose the iOS scope.",
                    "issue": "ISS-1001"},
        }, "check.md")
        self.assertEqual([], problems)
        check = rt.Check("TST-1004", "Android backup", "check.md", "Bench",
                           readiness_for=declared)
        entry = rt.Placed(rt.Section("Bench", surfaces=["Bench"]), [check])
        _section, ios = self.page_of(entry, "ios")
        _section, android = self.page_of(entry, "android")
        # A decision with no declared result offers `question` (REQ-0033).
        self.assertIn("_Choose the iOS scope. (ISS-1001) Suggested: Question._", ios)
        self.assertNotIn("Choose the iOS scope", android)

    def test_malformed_unscripted_check_readiness_is_reported(self):
        declared, problems = rt.parse_check_readiness({
            "ios": {"kind": "decision", "reason": "  "},
            "iOS": {"kind": "preparation", "reason": "Find the device."},
        }, "check.md")
        self.assertEqual({}, declared)
        self.assertEqual(2, len(problems))
        self.assertTrue(all("readiness_for" in problem for problem in problems))
        check = rt.Check("TST-1004", "Bad readiness", "check.md", "Bench",
                           readiness_for=declared, readiness_problems=problems)
        self.assertEqual("decision", rt.check_readiness(check, "ios")["kind"])
        entry = rt.Placed(rt.Section("Bench", surfaces=["Bench"]), [check])
        _section, rendered = self.page_of(entry, "ios")
        self.assertIn("readiness declaration is invalid", rendered)


if __name__ == "__main__":
    unittest.main()
