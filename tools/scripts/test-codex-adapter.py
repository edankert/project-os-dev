#!/usr/bin/env python3
"""Fixture checks for project-os Codex generated assets and hook decisions."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / 'tools/adapters/codex/hooks/dispatch.py'
GEN = ROOT / 'tools/scripts/generate-adapters.py'

class CodexAdapterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        (self.repo / 'docs/features/x/plan/tasks').mkdir(parents=True)
        (self.repo / 'docs/tests').mkdir()
        self.set_snapshot('')

    def set_snapshot(self, task=''):
        (self.repo / 'SNAPSHOT.yaml').write_text(f'''version: 1
template:
  replace_me: false
focus:
  task: "{task}"
  feature: "FEAT-0001"
  phase: "PHASE-0001"
  issue: ""
items:
  tasks:
    TASK-0001:
      status: doing
      tests: [TST-0001]
''')

    def call(self, event, name='', command='', cwd=None, **extra):
        payload = {'cwd': str(cwd or self.repo), 'session_id': 'codex-adapter-fixture', 'hook_event_name': event, 'tool_name': name, 'tool_input': {'command': command}, **extra}
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def patch(self, path, body):
        return f'*** Begin Patch\n*** Update File: {path}\n@@\n{body}\n*** End Patch'

    def test_document_first_denies_code_patch_without_focus(self):
        out = self.call('PreToolUse', 'apply_patch', self.patch('src/main.py', '+hello'))
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIn('HC-001', out['hookSpecificOutput']['permissionDecisionReason'])

    def test_document_first_allows_docs_and_tools(self):
        for path in ('docs/features/x.md', 'tools/script.py', '.codex/hooks.json'):
            with self.subTest(path=path):
                self.assertEqual(self.call('PreToolUse', 'apply_patch', self.patch(path, '+hello')), {})

    def test_target_repo_controls_cross_repo_edit(self):
        self.set_snapshot('TASK-0001')
        other = Path(self.tmp.name) / 'other'
        (other / 'src').mkdir(parents=True)
        (other / 'SNAPSHOT.yaml').write_text('focus:\n  task: ""\n  issue: ""\n')
        out = self.call('PreToolUse', 'apply_patch', self.patch(str(other/'src/main.py'), '+hello'))
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.call('PreToolUse', 'apply_patch', self.patch(str(Path(self.tmp.name)/'scratch.py'), '+hello')), {})

    def test_shell_redirection_is_gated_when_target_is_explicit(self):
        out = self.call('PreToolUse', 'Bash', 'echo hello > src/main.py')
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_template_placeholder_is_exempt(self):
        (self.repo/'SNAPSHOT.yaml').write_text('template:\n  replace_me: true\n')
        self.assertEqual(self.call('PreToolUse', 'apply_patch', self.patch('src/main.py', '+hello')), {})

    def test_verification_blocks_failing_manual_test(self):
        self.set_snapshot('TASK-0001')
        (self.repo/'docs/tests/TST-0001-X.md').write_text('---\nid: TST-0001\nstatus: failing\nlevel: system\n---\n')
        out = self.call('PreToolUse', 'apply_patch', self.patch('docs/features/x/plan/tasks/TASK-0001-X.md', '+status: done'))
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIn('TST-0001', out['hookSpecificOutput']['permissionDecisionReason'])

    def test_verification_exempts_command_and_acceptance(self):
        self.set_snapshot('TASK-0001')
        test = self.repo/'docs/tests/TST-0001-X.md'
        for lines in ('status: active\ncommand: pytest -q', 'status: active\nlevel: acceptance'):
            with self.subTest(lines=lines):
                test.write_text('---\nid: TST-0001\n'+lines+'\n---\n')
                self.assertEqual(self.call('PreToolUse', 'apply_patch', self.patch('docs/features/x/plan/tasks/TASK-0001-X.md', '+status: done')), {})

    def test_verification_requires_expiring_waiver(self):
        self.set_snapshot('TASK-0001')
        out = self.call('PreToolUse', 'apply_patch', self.patch('docs/features/x/plan/tasks/TASK-0001-X.md', '+status: done\n+verification_waiver: docs-only'))
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        out = self.call('PreToolUse', 'apply_patch', self.patch('docs/features/x/plan/tasks/TASK-0001-X.md', '+status: done\n+verification_waiver: docs-only\n+waiver_expires: 2026-12-01'))
        self.assertEqual(out, {})

    def test_post_advisory_and_stop_once(self):
        self.set_snapshot('TASK-0001')
        patch = self.patch('package.json', '+hello')
        out = self.call('PostToolUse', 'apply_patch', patch)
        self.assertIn('HC-005', out['hookSpecificOutput']['additionalContext'])
        out = self.call('Stop')
        self.assertEqual(out['decision'], 'block')
        self.assertIn('HC-006', out['reason'])
        self.assertEqual(self.call('Stop'), {})

    def test_session_and_prompt_hints(self):
        self.set_snapshot('TASK-0001')
        self.assertIn('SNAPSHOT.yaml', self.call('SessionStart')['hookSpecificOutput']['additionalContext'])
        self.assertIn('TASK-0001', self.call('UserPromptSubmit')['hookSpecificOutput']['additionalContext'])

    def test_session_start_serves_the_slice(self):
        # HC-002 (project-os-dev TASK-0080): with the slice script present, the
        # context is the orientation itself, not a reminder to go and read it.
        self.set_snapshot('TASK-0001')
        (self.repo / 'tools/scripts').mkdir(parents=True)
        (self.repo / 'tools/scripts/snapshot-slice.py').write_text((ROOT / 'tools/scripts/snapshot-slice.py').read_text())
        brief = self.call('SessionStart')['hookSpecificOutput']['additionalContext']
        self.assertIn('focus.task: TASK-0001 (doing)', brief)
        self.assertNotIn('Read CONTEXT.md', brief)

    def test_stop_quotes_open_boxes(self):
        # HC-006 (project-os-dev TASK-0157): the block names what is still open.
        self.set_snapshot('TASK-0001')
        snap = self.repo / 'SNAPSHOT.yaml'
        snap.write_text(snap.read_text().replace('      status: doing', '      file: docs/features/x/plan/tasks/TASK-0001.md\n      status: doing'))
        (self.repo / 'docs/features/x/plan/tasks/TASK-0001.md').write_text('# T\n## Definition of Done\n- [x] Done\n- [ ] Write the parser\n## Notes\n- [ ] Not work\n')
        self.call('PostToolUse', 'apply_patch', self.patch('package.json', '+hello'))
        reason = self.call('Stop')['reason']
        self.assertIn('1 unticked box(es): "Write the parser"', reason)
        self.assertNotIn('Not work', reason)

    def test_stop_ticked_missing_and_boxless_notes(self):
        # FEAT-0039 review round 1: the all-ticked branch, a focus task with no
        # snapshot item, and a note with no box sections.
        self.set_snapshot('TASK-0001')
        note = self.repo / 'docs/features/x/plan/tasks/TASK-0001-X.md'
        note.write_text('# T\n## Steps\n- [x] Done\n')
        self.call('PostToolUse', 'apply_patch', self.patch('package.json', '+hello'))
        self.assertIn('every box in its note is ticked', self.call('Stop')['reason'])
        note.write_text('# T\n## Notes\nnone\n')
        self.call('PostToolUse', 'apply_patch', self.patch('package.json', '+hello'))
        reason = self.call('Stop')['reason']
        self.assertNotIn('every box', reason)
        self.assertNotIn('unticked', reason)

    def test_prompt_hint_reads_quoted_snapshot_status(self):
        for status in ('doing', '"doing"', "'doing'"):
            with self.subTest(status=status):
                self.set_snapshot('TASK-0001')
                path = self.repo / 'SNAPSHOT.yaml'
                path.write_text(path.read_text().replace('status: doing', 'status: ' + status))
                hint = self.call('UserPromptSubmit')['hookSpecificOutput']['additionalContext']
                self.assertIn('TASK-0001 is doing,', hint)

    def test_generated_codex_files_and_drift(self):
        planner = (ROOT/'.codex/agents/planner.toml').read_text()
        self.assertIn('name = "planner"', planner)
        self.assertIn('developer_instructions = ', planner)
        self.assertTrue((ROOT/'.agents/skills/adapter-sync/SKILL.md').is_file())
        self.assertEqual(json.loads((ROOT/'.codex/hooks.json').read_text())['hooks']['PreToolUse'][0]['matcher'], '^(Bash|apply_patch)$')
        fixture = Path(self.tmp.name)/'generation'
        (fixture/'tools/skills/example').mkdir(parents=True)
        (fixture/'tools/skills/example/SKILL.md').write_text('# Skill: Example\n\n## When to use\n- Example work.\n')
        subprocess.run([sys.executable, str(GEN), '--repo-root', str(fixture)], check=True, capture_output=True, text=True)
        self.assertEqual(subprocess.run([sys.executable, str(GEN), '--repo-root', str(fixture), '--check'], capture_output=True).returncode, 0)
        p = fixture/'.agents/skills/example/SKILL.md'
        p.write_text('stale')
        self.assertEqual(subprocess.run([sys.executable, str(GEN), '--repo-root', str(fixture), '--check'], capture_output=True).returncode, 1)

    def test_install_preserves_existing_codex_hooks(self):
        fixture = Path(self.tmp.name)/'install'
        (fixture/'tools/skills/x').mkdir(parents=True)
        (fixture/'tools/skills/x/SKILL.md').write_text('# Skill: X\n')
        (fixture/'tools/adapters/codex').mkdir(parents=True)
        (fixture/'tools/adapters/codex/hooks.json').write_text('{"hooks":{"Stop":[]}}\n')
        (fixture/'.codex').mkdir()
        existing = '{"hooks":{"Custom":[]}}\n'
        (fixture/'.codex/hooks.json').write_text(existing)
        subprocess.run([sys.executable, str(GEN), '--repo-root', str(fixture), '--install-hooks'], check=True, capture_output=True, text=True)
        self.assertEqual((fixture/'.codex/hooks.json').read_text(), existing)
        subprocess.run([sys.executable, str(GEN), '--repo-root', str(fixture), '--install-hooks', '--force-hooks'], check=True, capture_output=True, text=True)
        self.assertEqual((fixture/'.codex/hooks.json').read_text(), '{"hooks":{"Stop":[]}}\n')

if __name__ == '__main__':
    unittest.main(verbosity=2)
