#!/usr/bin/env python3
"""The project-os plugin is registered in each repo by generate-adapters.py
(project-os-dev FEAT-0041, TASK-0199).

Each test builds a fixture repo in a temporary folder, runs the real generator
on it, and reads what it wrote: the repo's own marketplace file and the two
keys in .claude/settings.json that make Claude Code load the plugin.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / 'tools/scripts/generate-adapters.py'
SOURCE = {'source': {'source': 'directory', 'path': './'}}


class PluginRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'some-folder'
        (self.repo / 'tools/skills/example').mkdir(parents=True)
        (self.repo / 'tools/skills/example/SKILL.md').write_text('# Example\n')
        plugin = self.repo / 'tools/adapters/claude-code/plugin/.claude-plugin'
        plugin.mkdir(parents=True)
        (plugin / 'plugin.json').write_text('{"name": "project-os", "version": "0.1.0"}\n')
        self.name('Your Trainer')

    def name(self, value):
        (self.repo / 'SNAPSHOT.yaml').write_text(f'version: 1\nproject:\n  name: "{value}"\n  owner: someone\nfocus:\n  task: ""\n')

    def run_gen(self, *args):
        return subprocess.run([sys.executable, str(GEN), '--repo-root', str(self.repo), *args],
                              capture_output=True, text=True)

    def settings(self):
        return json.loads((self.repo / '.claude/settings.json').read_text())

    def write_settings(self, value):
        (self.repo / '.claude').mkdir(exist_ok=True)
        (self.repo / '.claude/settings.json').write_text(json.dumps(value))

    def test_marketplace_and_registration_carry_the_projects_own_name(self):
        out = self.run_gen('--install-hooks')
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        market = json.loads((self.repo / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(market['name'], 'project-os-your-trainer')
        self.assertEqual(market['plugins'][0]['name'], 'project-os')
        self.assertEqual(market['plugins'][0]['source'], './tools/adapters/claude-code/plugin')
        s = self.settings()
        self.assertEqual(s['extraKnownMarketplaces'], {'project-os-your-trainer': SOURCE})
        self.assertEqual(s['enabledPlugins'], {'project-os@project-os-your-trainer': True})

    def test_two_projects_get_two_names(self):
        self.run_gen('--install-hooks')
        first = self.settings()['enabledPlugins']
        self.name('project-os-cockpit')
        self.run_gen('--install-hooks')
        second = self.settings()['enabledPlugins']
        self.assertNotEqual(list(first), list(second))

    def test_the_placeholder_name_falls_back_to_the_folder(self):
        self.name('REPLACE ME')
        self.run_gen('--install-hooks')
        self.assertIn('project-os-some-folder', self.settings()['extraKnownMarketplaces'])

    def test_other_settings_are_kept(self):
        self.write_settings({'model': 'x', 'enabledPlugins': {'other@market': True},
                             'extraKnownMarketplaces': {'market': {'source': {'source': 'github', 'repo': 'a/b'}}}})
        self.run_gen('--install-hooks')
        s = self.settings()
        self.assertEqual(s['model'], 'x')
        self.assertTrue(s['enabledPlugins']['other@market'])
        self.assertIn('market', s['extraKnownMarketplaces'])

    def test_a_plugin_switched_off_stays_off(self):
        self.write_settings({'enabledPlugins': {'project-os@project-os-your-trainer': False}})
        self.run_gen('--install-hooks')
        self.assertIs(self.settings()['enabledPlugins']['project-os@project-os-your-trainer'], False)
        self.assertEqual(self.run_gen('--check').returncode, 0)

    def test_a_renamed_project_replaces_the_old_registration_and_keeps_its_switch(self):
        self.write_settings({'extraKnownMarketplaces': {'project-os-old-name': SOURCE},
                             'enabledPlugins': {'project-os@project-os-old-name': False}})
        self.run_gen('--install-hooks')
        s = self.settings()
        self.assertEqual(list(s['extraKnownMarketplaces']), ['project-os-your-trainer'])
        self.assertEqual(s['enabledPlugins'], {'project-os@project-os-your-trainer': False})

    def test_check_passes_when_registered_and_fails_when_the_registration_is_removed(self):
        self.run_gen('--install-hooks')
        ok = self.run_gen('--check')
        self.assertEqual(ok.returncode, 0, ok.stdout)
        s = self.settings()
        del s['extraKnownMarketplaces']['project-os-your-trainer']
        self.write_settings(s)
        bad = self.run_gen('--check')
        self.assertEqual(bad.returncode, 1)
        self.assertIn('UNREGISTERED', bad.stdout)
        s['extraKnownMarketplaces']['project-os-your-trainer'] = SOURCE
        del s['enabledPlugins']['project-os@project-os-your-trainer']
        self.write_settings(s)
        self.assertEqual(self.run_gen('--check').returncode, 1)

    def test_check_reports_a_stale_marketplace_file(self):
        self.run_gen('--install-hooks')
        (self.repo / '.claude-plugin/marketplace.json').write_text('{}\n')
        out = self.run_gen('--check')
        self.assertEqual(out.returncode, 1)
        self.assertIn('STALE .claude-plugin/marketplace.json', out.stdout)

    def test_the_committed_state_check_sees_the_folder_name_a_clone_would_have(self):
        # validate-docs.sh --as-committed unpacks HEAD into a temporary folder
        # and runs generate-adapters --check there. With no project name the
        # marketplace name comes from the folder, so the copy must keep the
        # repo's folder name (project-os-dev TASK-0204).
        import shutil
        self.name('REPLACE ME')
        scripts = self.repo / 'tools/scripts'
        scripts.mkdir(parents=True)
        shutil.copy(ROOT / 'tools/scripts/validate-docs.sh', scripts)
        shutil.copy(GEN, scripts)
        # The notes validator is not under test here.
        (scripts / 'validate-docs.py').write_text('import sys\nsys.exit(0)\n')
        self.assertEqual(self.run_gen('--install-hooks').returncode, 0)
        git = ['git', '-C', str(self.repo), '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false']
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(git + ['add', '-A'], check=True)
        subprocess.run(git + ['commit', '-q', '--no-verify', '-m', 'fixture'], check=True)
        out = subprocess.run(['bash', str(scripts / 'validate-docs.sh'), '--as-committed'],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn('HEAD passes the full CI step set', out.stdout)

    def test_a_repo_without_the_plugin_folder_registers_nothing(self):
        import shutil
        shutil.rmtree(self.repo / 'tools/adapters/claude-code/plugin')
        self.run_gen('--install-hooks')
        self.assertFalse((self.repo / '.claude-plugin/marketplace.json').exists())
        settings = self.repo / '.claude/settings.json'
        self.assertFalse(settings.exists() and 'enabledPlugins' in json.loads(settings.read_text()))
        self.assertEqual(self.run_gen('--check').returncode, 0)


if __name__ == '__main__':
    unittest.main()
