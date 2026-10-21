#!/usr/bin/env python3
"""A command per platform, hand steps, the budget line, the ride script and its import.

project-os-dev TASK-0205 (ISS-0108) and TASK-0206 (ISS-0109). One fixture repo
with an Android and an iOS ledger, seven acceptance checks, one section tested
from a procedure, one section printed check by check, one Unplaced check and
one changed screen. Each case asserts what a tester or the app would notice:
which steps are owed on which platform, what the sheet prints, what
`--check` refuses, what the ride script holds and what the import writes.

Exit 0 = every assertion holds.
"""

import sys as _sys
# No bytecode, ever: a cached compile Python judges current is used in place of
# the source (project-os-dev ISS-0073).
_sys.dont_write_bytecode = True

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "release-test.py"
spec = importlib.util.spec_from_file_location("release_ride_test", SCRIPT)
rt = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rt
spec.loader.exec_module(rt)
vd = rt._validator()

failures = 0
count = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global failures, count
    count += 1
    if not ok:
        failures += 1
        print("  FAIL %s%s" % (label, ": " + detail if detail else ""))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def note(cid: str, area: str, extra: str, steps: list[str], expect: list[str], setup: str = "") -> str:
    body = "".join("%d. %s\n" % (i, s) for i, s in enumerate(steps, start=1)) if steps else ""
    return ("---\ntype: \"[[test]]\"\nid: %s\ntitle: \"The %s check\"\nstatus: active\nowner: user:fixture\n"
            "scope: system\nlevel: acceptance\narea: \"%s\"\n%s---\n\n# The %s check\n\n%s"
            "## Steps\n%s\n## Expect\n%s"
            % (cid, cid, area, extra, cid, "## Setup\n%s\n\n" % setup if setup else "",
               body or "Open the panel and look at it.\n", "".join("- %s\n" % e for e in expect)))


PROCEDURE = """---
type: "[[reference]]"
title: "Procedure — Bench"
status: active
section: "Bench"
step_platforms:
  3: [ios]
  5: [ios]
requires:
  4: [2]
setup_for:
  kickr: all
  strap: [4]
---

# Procedure — Bench

## Setup
- [kickr] The KICKR is awake.
- [strap] The strap is on.

## Steps

### Riding
Start: A ride is open.

1. Pedal for a minute.
   - `TST-0001.1`
   - `TST-0001.2`
2. Tap Connect on the strap row.
3. Open the panel.
   - `TST-0002.1`
4. Read the strap row.
   - `TST-0002.2`
5. Read the log.
   - `TST-0002.3`
   - `TST-0003.1`
"""


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "f", "GIT_AUTHOR_EMAIL": "f@x", "GIT_COMMITTER_NAME": "f",
                        "GIT_COMMITTER_EMAIL": "f@x", "PATH": "/usr/bin:/bin:/usr/local/bin"})


def build_fixture(root: Path, limit: str = "") -> Path:
    repo = root / "fixture"
    docs = repo / "docs"
    write(repo / "SNAPSHOT.yaml", 'version: 1\nupdated: "2026-10-21T00:00Z"\ntemplate:\n  replace_me: false\n'
          'counters:\n  TST: 7\nfocus:\n  task: ""\n  feature: ""\n  phase: ""\n  issue: ""\nitems: {}\n')
    acc = docs / "tests" / "acceptance"
    write(acc / "TST-0001-A.md", note("TST-0001", "Alpha", "", ["Pedal.", "Read power."],
                                      ["The wheel turns.", "Power reads 100 W."]))
    write(acc / "TST-0002-A.md", note("TST-0002", "Alpha", 'commands: {android: "make test-android"}\nhand_steps: [2]\n',
                                      ["Open the panel.", "Read the strap.", "Read the log."],
                                      ["The panel opens.", "The strap reads 120 bpm.", "The log lists the strap."]))
    write(acc / "TST-0003-A.md", note("TST-0003", "Alpha", 'commands: {android: "make test-android"}\n',
                                      ["Read the log."], ["The log is complete."]))
    write(acc / "TST-0004-B.md", note("TST-0004", "Beta", 'commands: {android: "make test-android"}\nhand_steps: [3]\n',
                                      ["Open settings.", "Turn it on.", "Look at the colours."],
                                      ["Settings open.", "It is on.", "The colours match the theme."],
                                      setup="A rider exists."))
    write(acc / "TST-0005-B.md", note("TST-0005", "Beta", 'command: "make test"\n', ["Run it."], ["It runs."]))
    write(acc / "TST-0006-B.md", note("TST-0006", "Beta", "", [], ["The panel looks right."]))
    write(acc / "TST-0007-C.md", note("TST-0007", "Gamma", "", ["Open it.", "Close it."], ["It opens.", "It closes."]))
    write(acc / "RELEASE-TEST.md", "---\ntype: \"[[reference]]\"\ntitle: \"Section order\"\nstatus: active\n%s---\n\n"
          "# Section order\n\n### Bench\n\n```yaml\nsurfaces: [\"Alpha\"]\n```\n\n### Rows\n\n```yaml\n"
          "surfaces: [\"Beta\"]\n```\n" % limit)
    write(acc / "release-test" / "bench.md", PROCEDURE)
    write(docs / "surfaces" / "SUR-0001-Panel.md", "---\ntype: \"[[surface]]\"\nid: SUR-0001\ntitle: \"Panel\"\n"
          "status: active\nkind: screen\n---\n\n# Panel\n")
    for platform in ("android", "ios"):
        write(docs / "releases" / "ledgers" / ("WORKING-%s.json" % platform),
              rt.ledger_text({"platform": platform, "entries": [], "evidence": []}))
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    git(repo, "tag", "v1.0")
    write(docs / "releases" / "REL-0001-v1.0.md", "---\ntype: \"[[release]]\"\nid: REL-0001\ntitle: \"v1.0\"\n"
          "status: released\ndate: 2026-10-01\ntag: v1.0\n---\n\n# v1.0\n")
    write(docs / "changes" / "CHG-20261020-The-Panel-Moves.md", "---\ntype: \"[[change]]\"\nid: CHG-20261020\n"
          "title: \"The panel moves\"\nstatus: active\ncreated: 2026-10-20\nplatforms: [android]\n---\n\n"
          "# The panel moves\n\n## Impact\n- SUR-0001: The panel moved to the left.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "change")
    return repo


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True)


def parts(sheet, check_id: str) -> list[str]:
    """Every expectation tag the sheet's payload prints for one check."""
    out = []
    for section in rt.payload(sheet)["sections"]:
        for group in section["groups"]:
            for printed in group["checks"]:
                out += [t for t in printed["tags"] if t.split(".")[0] == check_id]
    return out


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    try:
        repo = build_fixture(tmp)
        android = rt.generate(repo, "REL-0002", "android")
        ios = rt.generate(repo, "REL-0002", "ios")
        owed_android = {c.id for c in rt.owed_checks(rt.read_repo(repo, "android").checks, [], "android")}
        owed_ios = {c.id for c in rt.owed_checks(rt.read_repo(repo, "ios").checks, [], "ios")}

        # Rule 1: a command can cover one platform.
        check("commands.android takes a check off the Android sheet", "TST-0003" not in owed_android)
        check("commands.android leaves the check owed on iOS", "TST-0003" in owed_ios)
        check("command: takes a check off every platform", "TST-0005" not in owed_android | owed_ios)
        check("a check with no command is owed on both", "TST-0001" in owed_android & owed_ios)
        check("the cockpit's question, with no platform, still counts only command:",
              "TST-0003" in {c.id for c in rt.owed_checks(rt.read_repo(repo, "ios").checks, [])})

        # Rule 2: hand steps stay owed where the command covers the check.
        check("hand_steps keeps the check owed on Android", "TST-0002" in owed_android)
        check("the procedure prints only the hand step on Android", parts(android, "TST-0002") == ["TST-0002.2"],
              str(parts(android, "TST-0002")))
        check("every step stays owed on iOS", parts(ios, "TST-0002") == ["TST-0002.1", "TST-0002.2", "TST-0002.3"],
              str(parts(ios, "TST-0002")))
        text = rt.render(android)
        row = text[text.index("The TST-0004 check"):]
        row = row[:row.index("\n- [ ]") if "\n- [ ]" in row else len(row)]
        check("a per-check row prints only its hand step", "Look at the colours." in row
              and "Open settings." not in row and "Turn it on." not in row, row)
        check("a per-check row prints only its hand step's Expect line", "The colours match the theme." in row
              and "Settings open." not in row, row)
        check("a per-check row tags its hand step", "`TST-0004.3`" in row, row)
        ios_text = rt.render(ios)
        check("on iOS the same row prints every step", "Open settings." in ios_text and "Look at the colours." in ios_text)
        problems, _remarks = rt.check_repo(repo, "android")
        check("the procedure that limits command-covered steps to iOS passes --check on Android", problems == [],
              "; ".join(problems))
        # TASK-0207: a step shared by both platforms may cite a part only iOS still needs.
        shared = PROCEDURE.replace("  3: [ios]\n", "")
        write(repo / "docs/tests/acceptance/release-test/bench.md", shared)
        problems, _remarks = rt.check_repo(repo, "android")
        check("a shared step may cite a part the Android command covers while iOS still needs it",
              not any("a command tests" in p for p in problems), "; ".join(problems))
        shared_android = rt.generate(repo, "REL-0002", "android")
        check("and the Android sheet still prints only the hand step", parts(shared_android, "TST-0002") == ["TST-0002.2"],
              str(parts(shared_android, "TST-0002")))
        problems, _remarks = rt.check_repo(repo, "ios")
        check("the same procedure is fine on iOS, where no command covers the check",
              not any("a command tests" in p for p in problems), "; ".join(problems))
        android_only = PROCEDURE.replace("  3: [ios]\n", "  3: [android]\n")
        write(repo / "docs/tests/acceptance/release-test/bench.md", android_only)
        problems, _remarks = rt.check_repo(repo, "android")
        check("--check refuses a step that runs only where a command covers its part",
              any("TST-0002.1" in p and "a command tests TST-0002 except steps 2" in p for p in problems),
              "; ".join(problems))
        write(repo / "docs/tests/acceptance/release-test/bench.md", PROCEDURE)
        three = repo / "docs/tests/acceptance/TST-0003-A.md"
        kept = three.read_text(encoding="utf-8")
        write(three, kept.replace('commands: {android: "make test-android"}', 'command: "make test"'))
        problems, _remarks = rt.check_repo(repo, "ios")
        check("--check refuses a citation of a check `command:` covers on every platform",
              any("TST-0003.1" in p and "a command tests TST-0003" in p for p in problems), "; ".join(problems))
        write(three, kept)

        # The validator: commands: and hand_steps: are read and checked.
        def findings(extra: str, steps=("One.", "Two.")) -> list[str]:
            path = repo / "docs/tests/acceptance/TST-0099-X.md"
            write(path, note("TST-0099", "Alpha", extra, list(steps), ["A.", "B."]))
            fm = vd.parse_frontmatter(path)
            report = vd.Report()
            vd.validate_check_commands(repo, report, {"TST-0099": (path, fm)})
            path.unlink()
            return [m for m in report.errors if "CHECK-COMMANDS" in m]
        check("well-formed commands: and hand_steps: draw nothing",
              findings('commands: {android: "make a"}\nhand_steps: [2]\n') == [])
        check("a hand step the note does not have is refused",
              any("names step 3" in m for m in findings('commands: {android: "make a"}\nhand_steps: [3]\n')))
        check("hand_steps that is not a list of numbers is refused",
              len(findings('commands: {android: "make a"}\nhand_steps: two\n')) == 1)
        check("hand_steps with no command is refused", any("no `command:` or `commands:`" in m
                                                          for m in findings("hand_steps: [1]\n")))
        check("an empty command in commands: is refused", len(findings('commands: {android: ""}\n')) == 1)
        older = repo / "docs/tests/acceptance/TST-0097-X.md"
        write(older, note("TST-0097", "Alpha", 'commands: {android: "make a"}\nhand_steps: [2]\n', ["One.", "Two."],
                          ["A.", "B."]).replace("## Steps", "## Procedure"))
        report = vd.Report()
        vd.validate_check_commands(repo, report, {"TST-0097": (older, vd.parse_frontmatter(older))})
        older.unlink()
        check("hand steps count the items under the older `## Procedure` heading (TASK-0207)",
              not [m for m in report.errors if "CHECK-COMMANDS" in m], "; ".join(report.errors))
        check("a platform with no ledger in commands: is refused",
              any("platform andriod" in m for m in findings('commands: {andriod: "make a"}\n')))
        check("command: beside commands: is refused",
              any("both `command:` and `commands:`" in m for m in findings('command: "make"\ncommands: {ios: "make"}\n')))
        check("commands: that is not a map is refused", len(findings('commands: "make"\n')) == 1)
        stray = repo / "docs/tests/acceptance/TST-0098-X.md"
        write(stray, note("TST-0098", "Alpha", "hand_steps: [1]\n", ["One."], ["A."]))
        validated = subprocess.run([sys.executable, "-B", str(HERE / "validate-docs.py"), "--repo-root", str(repo)],
                                   capture_output=True, text=True)
        check("the validator's own run reaches the check", "[CHECK-COMMANDS] TST-0098" in validated.stdout + validated.stderr,
              (validated.stdout + validated.stderr)[-600:])
        stray.unlink()

        # Rule 3: each sheet prints a budget line, and --json carries it.
        check("the Android sheet prints its budget near the top",
              "**Hand-run budget:** 5 checks with 7 steps are owed by hand on Android. The limit is 10 checks."
              in "\n".join(text.splitlines()[:12]), "\n".join(text.splitlines()[:12]))
        page = rt.payload(android)
        check("--json carries the budget", page["budget"] == {"limit": 10, "checks": 5, "steps": 7, "over": 0},
              str(page["budget"]))
        limited = build_fixture(tmp / "limited", limit="hand_run_limit: 2\n")
        over = rt.render(rt.generate(limited, "REL-0002", "android"))
        check("a project's own limit is read from RELEASE-TEST.md, and the line says how far over",
              "The limit is 2 checks. This release is 3 over it." in over)
        bad = build_fixture(tmp / "bad", limit="hand_run_limit: ten\n")
        problems, _remarks = rt.check_repo(bad, "android")
        check("a hand_run_limit that is not a number is refused by --check",
              any("`hand_run_limit` is 'ten'" in p for p in problems), "; ".join(problems))

        # The ride script.
        out = tmp / "ride" / "script.json"
        done = run("--repo-root", str(repo), "--release", "REL-0002", "--platform", "android", "--ride-script", str(out))
        check("--ride-script exits 0", done.returncode == 0, done.stderr)
        script = json.loads(out.read_text(encoding="utf-8"))
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        check("the script carries its format, release, platform and commit",
              (script["format"], script["release"], script["platform"], script["commit"])
              == ("release-ride-script/1", "REL-0002", "android", head))
        check("the script carries the budget, and one step per hand step",
              script["budget"] == {"limit": 10, "checks": 5, "steps": 7} and len(script["steps"]) == 7,
              str(script["budget"]))
        ids = [s["id"] for s in script["steps"]]
        check("the steps are in the sheet's order",
              ids == ["TST-0001.1", "TST-0001.2", "TST-0002.2", "TST-0004.3", "TST-0006", "TST-0007.1",
                      "TST-0007.2"], str(ids))
        by_id = {s["id"]: s for s in script["steps"]}
        first = by_id["TST-0001.1"]
        check("a step names its section, group and setup items",
              (first["section"], first["heading"], first["setup"]) == (1, "Riding", ["kickr"]), str(first))
        check("a group's start state opens the first step's action",
              first["do"] == "Start: A ride is open.\nPedal for a minute.", repr(first["do"]))
        check("a step's expect is the check's own line for that part", first["expect"] == ["The wheel turns."])
        check("a second part of one action does not repeat it", by_id["TST-0001.2"]["do"] == rt.SAME_ACTION)
        strap = by_id["TST-0002.2"]
        check("a preparation step's action leads the next owed step",
              strap["do"] == "Tap Connect on the strap row.\nRead the strap row.", repr(strap["do"]))
        check("a setup item scoped to steps is named only on them", strap["setup"] == ["kickr", "strap"])
        row_step = by_id["TST-0004.3"]
        check("a per-check row's step is its hand step, with its Setup first",
              row_step["do"] == "Setup: A rider exists.\nLook at the colours."
              and row_step["expect"] == ["The colours match the theme."] and row_step["setup"] == [], str(row_step))
        check("an Unplaced check has no section number", by_id["TST-0007.1"]["section"] is None)
        check("the script lists the changed screen with its line",
              script["screens"] == [{"surface": "SUR-0001", "name": "Panel",
                                     "changes": ["The panel moved to the left."]}], str(script["screens"]))
        ios_script = rt.ride_script(ios)
        check("the iOS script holds every step of TST-0002",
              [s["id"] for s in ios_script["steps"] if s["check"] == "TST-0002"]
              == ["TST-0002.1", "TST-0002.2", "TST-0002.3"])
        check("the iOS script lists no screen, since the change was Android only", ios_script["screens"] == [])

        # The import.
        ride = tmp / "ride"
        write(ride / "TST-0002.2-screen.png", "picture")
        results = {
            "format": "release-ride-results/1", "release": "REL-0002", "platform": "android",
            "build": {"versionName": "2.2.0", "versionCode": 123, "buildType": "release"},
            "script_commit": head, "started": "2026-10-21T18:00:00Z", "finished": "2026-10-21T18:31:00Z",
            "by": "user:edwin",
            "steps": [
                {"id": "TST-0001.1", "result": "pass", "how": "person", "note": "", "evidence": []},
                {"id": "TST-0001.2", "result": "pass", "how": "app", "note": "", "evidence": []},
                {"id": "TST-0002.2", "result": "fail", "how": "person", "note": "Strap lost.",
                 "evidence": ["TST-0002.2-screen.png", "missing.txt"]},
                {"id": "TST-0002.1", "result": "pass", "how": "person", "note": "", "evidence": []},
                {"id": "TST-0004.3", "result": "skip", "how": "person", "note": "", "evidence": []},
                {"id": "TST-0006", "result": "pass", "how": "person", "note": "", "evidence": []},
                {"id": "TST-0007.1", "result": "pass", "how": "person", "note": "", "evidence": []},
                {"id": "TST-0005.1", "result": "pass", "how": "person", "note": "", "evidence": []},
            ],
            "screens": [{"surface": "SUR-0001", "result": "fail", "note": "The panel overlaps the bar."}],
        }
        results_file = ride / "results-REL-0002-20261021T180000Z.json"
        write(results_file, json.dumps(results))
        ledger = repo / "docs/releases/ledgers/WORKING-android.json"
        before = ledger.read_text(encoding="utf-8")
        dry = run("--repo-root", str(repo), "--import-ride", str(results_file), "--platform", "android", "--dry-run")
        check("--dry-run exits 0 and writes nothing", dry.returncode == 0
              and ledger.read_text(encoding="utf-8") == before
              and not (repo / "docs/releases/ledgers/evidence").exists(), dry.stderr)
        check("--dry-run says what it would add", "would add 3 entries" in dry.stdout, dry.stdout)
        done = run("--repo-root", str(repo), "--import-ride", str(results_file), "--platform", "android")
        check("--import-ride exits 0", done.returncode == 0, done.stderr)
        data = json.loads(ledger.read_text(encoding="utf-8"))
        entries = {e["check"]: e for e in data["entries"]}
        check("every owed step passed: a pass", entries.get("TST-0001") == {
            "check": "TST-0001", "result": "pass", "date": "2026-10-21", "method": "ride",
            "by": "user:edwin", "build": "2.2.0 (123)"}, str(entries.get("TST-0001")))
        check("a check with no numbered steps passes on its one part", entries.get("TST-0006", {}).get("result") == "pass")
        check("a failed step: a fail, with its note as the reason",
              entries.get("TST-0002", {}).get("result") == "fail"
              and entries["TST-0002"].get("reason") == "TST-0002.2: Strap lost.", str(entries.get("TST-0002")))
        check("a skipped step adds nothing", "TST-0004" not in entries)
        check("a step missing from the results adds nothing", "TST-0007" not in entries)
        check("a check no longer owed adds nothing", "TST-0005" not in entries)
        folder = repo / "docs/releases/ledgers/evidence/REL-0002-android-20261021T180000Z"
        check("the evidence is copied beside the ledger", (folder / "TST-0002.2-screen.png").is_file())
        check("the ledger lists the evidence with its entry and step", data["evidence"] == [{
            "check": "TST-0002", "date": "2026-10-21",
            "ref": "docs/releases/ledgers/evidence/REL-0002-android-20261021T180000Z/TST-0002.2-screen.png",
            "note": "TST-0002.2"}], str(data["evidence"]))
        check("the import names the failed screen for an issue",
              "SUR-0001: The panel overlaps the bar." in done.stdout, done.stdout)
        check("the import says which checks stay owed, and why results were ignored",
              "stays owed: TST-0004" in done.stdout and "stays owed: TST-0007" in done.stdout
              and "TST-0002.1: not a step TST-0002 owes by hand on android" in done.stdout
              and "TST-0005: not owed on android any more" in done.stdout
              and "missing.txt is not beside the results file" in done.stdout, done.stdout)
        check("the ledger keeps one entry per line", ledger.read_text(encoding="utf-8") == rt.ledger_text(data))
        report = vd.Report()
        index, _ = vd.build_note_index(repo / "docs")
        vd.validate_ledgers(repo, report, index)
        check("the ledger checks accept the imported entries", report.errors == [], "; ".join(report.errors))
        again = run("--repo-root", str(repo), "--import-ride", str(results_file), "--platform", "android")
        check("importing the same ride twice adds nothing",
              len(json.loads(ledger.read_text(encoding="utf-8"))["entries"]) == 3
              and "already in WORKING-android.json" in again.stdout, again.stdout)
        owed_now = [c.id for c in rt.owed_checks(rt.read_repo(repo, "android").checks,
                                                 rt.load_events(repo / "docs", "android"), "android")]
        check("after the import the sheet owes the failed, skipped and unfinished checks",
              owed_now == ["TST-0002", "TST-0004", "TST-0007"], str(owed_now))
        wrong = run("--repo-root", str(repo), "--import-ride", str(results_file), "--platform", "ios")
        check("a results file for another platform is refused", wrong.returncode == 2
              and "is for platform 'android'" in wrong.stderr, wrong.stderr)

        # The ledger checks: method ride, and the build it names.
        def ledger_errors(entry: dict) -> list[str]:
            path = tmp / "lc" / "docs/releases/ledgers/WORKING-app.json"
            write(path, json.dumps({"platform": "app", "entries": [entry]}))
            report = vd.Report()
            vd.validate_ledgers(tmp / "lc", report, {})
            return report.errors
        good = {"check": "TST-0001", "result": "pass", "date": "2026-10-21", "method": "ride", "by": "user:edwin",
                "build": "2.2.0 (123)"}
        check("a ride entry with its build is accepted", ledger_errors(good) == [])
        check("a ride entry with no build is refused",
              any("names no `build`" in m for m in ledger_errors({k: v for k, v in good.items() if k != "build"})))
        check("an empty build is refused", any("empty `build`" in m for m in ledger_errors(dict(good, build=" "))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("test-release-ride: %d assertions, %d failure(s)" % (count, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
