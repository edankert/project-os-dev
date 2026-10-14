// The project-os plugin's three behaviours (project-os-dev FEAT-0041,
// TASK-0200 to TASK-0202).
//
// Run with `claude plugin test tools/adapters/claude-code/plugin`. The test's
// own hooks stand for the world beneath the plugin: `process.run` answers the
// repo's scripts (git, the routing hint, the validator, the marker writer) and
// records each call; `fs.read` is the repo's .claude/settings.json; and
// `session.*` are the session's root, id and model.

import type { On } from 'claude-code'
import { describe, expect, test } from 'claude-code/testing'
import { honoursPin, lineText, modelKey, parseHint, parseValidator, takeSegments } from '../hooks/register.ts'

const ROOT = '/repo'
const HINT_DOING = "project-os: focus item FEAT-0157 is 'doing', phase PHASE-046 (execution): implement here. For new work outside it: ..."
const VALIDATOR = 'ERROR [ITEM-STATUS] TASK-1 drift\nERROR [LINK] x\nWARN  [REVIEW-STALE] ADR-1 is accepted\nvalidate-docs: FAIL (notes: FAIL)\n'

type World = {
  runs: string[][]
  /** The fingerprints git hands out, in order; the last one repeats. */
  prints: string[]
  hint: string
  validator: string | undefined
  settings: string | undefined
  model: string
  /** Whether the world draws an empty band beneath the plugin, as the engine
   *  does; a test that draws its own beneath turns it off. */
  band: boolean
}

function world(on: On, w: Partial<World> = {}): World {
  const s: World = {
    runs: [], prints: ['all-1\ndocs-1\n'], hint: HINT_DOING, validator: VALIDATOR,
    settings: '{"model": "claude-opus-5-5"}', model: 'claude-opus-5-5', band: true, ...w,
  }
  on('session.root', () => ({ value: ROOT }))
  on('session.id', () => ({ value: 's-1' }))
  on('session.model', () => ({ value: s.model }))
  on('fs.read', ($, e, next) => {
    if (e.path !== `${ROOT}/.claude/settings.json`) return next(e)
    if (s.settings === undefined) throw new Error('ENOENT')
    return { value: s.settings }
  })
  on('process.run', ($, e) => {
    const argv = [...e.argv]
    s.runs.push(argv)
    const ok = (stdout: string, exitCode = 0) => ({ value: { exitCode, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
    if (argv[1] === '-c' && argv[2]?.includes('git rev-parse')) {
      const next = s.prints.length > 1 ? s.prints.shift()! : s.prints[0]!
      return next === 'not-a-repo' ? ok('', 3) : ok(next)
    }
    if (argv[1] === '-c' && argv[2]?.includes('session_marker')) return ok('')
    if (argv[1]?.endsWith('model-routing-hint.sh')) return ok(s.hint)
    if (argv[1] === 'tools/scripts/validate-docs.sh') {
      if (s.validator === undefined) throw new Error('timed out')
      return ok(s.validator, 1)
    }
    return ok('')
  })
  on('classic.Stop', () => ({}))
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  if (s.band) {
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)
      return h(Box, {})
    })
  }
  return s
}

const markers = (w: World) => w.runs.filter(r => r[1] === '-c' && r[2]?.includes('session_marker'))

/** Lets the plugin's background work (never awaited by a hook) finish. */
const settle = () => new Promise(r => setTimeout(r, 30))

const BAND = {
  component: 'AbovePrompt' as const,
  props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 120, scroll: { bodyRows: 9, offset: 0 }, view: {} } as any,
}

describe('a file changed from the shell counts as a write (TASK-0200)', () => {
  test('a turn that changes the working tree leaves the marker, for this session', async ($, on) => {
    const w = world(on, { prints: ['all-1\ndocs-1\n', 'all-2\ndocs-1\n'] })
    await $.turn.start({ text: 'sed it', turnId: 't-1' })
    await $.classic.Stop({ session_id: 's-1', stop_hook_active: false })
    expect(markers(w)).toHaveLength(1)
    expect(markers(w)[0]).toContain('s-1')
    expect(markers(w)[0]!.some(a => a.endsWith('/hooks/shared/session-marker.sh'))).toBe(true)
  })

  test('a turn that only reads leaves no marker', async ($, on) => {
    const w = world(on, { prints: ['all-1\ndocs-1\n', 'all-1\ndocs-1\n'] })
    await $.turn.start({ text: 'look', turnId: 't-1' })
    await $.classic.Stop({ session_id: 's-1', stop_hook_active: false })
    expect(markers(w)).toHaveLength(0)
  })

  test('outside a git repository nothing is written and the stop goes on', async ($, on) => {
    const w = world(on, { prints: ['not-a-repo'] })
    await $.turn.start({ text: 'x', turnId: 't-1' })
    await $.classic.Stop({ session_id: 's-1', stop_hook_active: false })
    expect(markers(w)).toHaveLength(0)
  })

  test("a subagent's turn does not reset the baseline", async ($, on) => {
    const w = world(on, { prints: ['all-1\ndocs-1\n', 'all-2\ndocs-1\n'] })
    await $.turn.start({ text: 'main', turnId: 't-1' })
    await $.turn.start({ text: 'sub', turnId: 't-2', agentId: 'agent-1' })
    await $.classic.Stop({ session_id: 's-1', stop_hook_active: false })
    expect(markers(w)).toHaveLength(1)
  })
})

describe('the session runs on the pinned model (TASK-0201)', () => {
  test('model names compare in one spelling', () => {
    expect(modelKey('claude-opus-5-5')).toBe('opus-5-5')
    expect(modelKey('Claude Opus 5.5')).toBe('opus-5-5')
    expect(modelKey('claude-sonnet-5-5-20261001')).toBe('sonnet-5-5')
    expect(honoursPin('claude-opus-5-5', 'opus')).toBe(true)
    expect(honoursPin('claude-sonnet-5-5', 'opus')).toBe(false)
    expect(honoursPin('claude-opus-5-5[1m]', 'claude-opus-5-5')).toBe(true)
    expect(honoursPin('claude-opus-5', 'claude-opus-5-5')).toBe(false)
  })

  test('a different model draws the warning row and adds it to the context', async ($, on) => {
    world(on, { model: 'claude-sonnet-5-5' })
    on('prompt.context', () => ({ blocks: [] }))
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    const row = await ui.find({ type: 'Text', text: /This session runs claude-sonnet-5-5; this repo pins claude-opus-5-5/ })
    expect(row).toBeDefined()
    const ctx = await $.prompt.context({ blocks: [] } as any)
    expect(ctx.blocks.some(b => b.name === 'projectOsModel' && b.text.includes('claude-sonnet-5-5'))).toBe(true)
  })

  test('the pinned model draws no warning', async ($, on) => {
    world(on, { model: 'claude-opus-5-5' })
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    expect(await ui.find({ type: 'Text', text: /This session runs/ })).toBeUndefined()
  })

  test('a repo with no pin draws no warning', async ($, on) => {
    world(on, { model: 'claude-sonnet-5-5', settings: '{"hooks": {}}' })
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    expect(await ui.find({ type: 'Text', text: /This session runs/ })).toBeUndefined()
  })
})

describe('the project line (TASK-0202)', () => {
  test('its facts come from the hint and the validator', () => {
    const facts = { ...parseHint(HINT_DOING), ...parseValidator({ exitCode: 1, stdout: VALIDATOR, stderr: '' }) }
    expect(lineText(facts)).toBe('FEAT-0157 doing · PHASE-046 · 2 validator errors · 1 review-stale · route: implement here')
    expect(lineText(parseHint('project-os: no focus item resolved: nothing in flight. ...'))).toBe('no focus item')
    expect(parseValidator({ exitCode: 0, stdout: 'validate-docs: OK (x)\n', stderr: '' })).toEqual({ errors: 0, reviewStale: 0 })
  })

  test('a validator that did not finish leaves its counts out, never zero', () => {
    expect(parseValidator(undefined)).toBeUndefined()
    expect(parseValidator({ exitCode: 1, stdout: 'Traceback (most recent call last)\n', stderr: '' })).toBeUndefined()
    expect(lineText({ ...parseHint(HINT_DOING) })).toBe('FEAT-0157 doing · PHASE-046 · route: implement here')
  })

  test('the line is drawn from the facts read at session start', async ($, on) => {
    world(on)
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    const line = await ui.find({ key: 'project-os:line' })
    expect(line).toBeDefined()
    expect(line!.text).toContain('FEAT-0157 doing · PHASE-046 · 2 validator errors · 1 review-stale · route: implement here')
  })

  test('a validator that times out leaves the count off the drawn line', async ($, on) => {
    world(on, { validator: undefined })
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    const line = await ui.find({ key: 'project-os:line' })
    expect(line!.text).not.toContain('validator')
  })

  test("another plugin's segment beneath is joined to the end of the line", async ($, on) => {
    world(on, { band: false })
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box, Text } = $.ui.resolve(e)
      return h(Box, { key: 'segment:test', flexDirection: 'row' }, h(Text, {}, ' · 3 need you'))
    })
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    const line = await ui.find({ key: 'project-os:line' })
    expect(line!.text).toMatch(/route: implement here.* · 3 need you$/)
  })

  test('a survey passes through untouched', async ($, on) => {
    world(on, { band: false })
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Text } = $.ui.resolve(e)
      return h(Text, {}, 'How was this session?')
    })
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND, props: { ...BAND.props, hasSurvey: true } })
    expect(await ui.find({ key: 'project-os:line' })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: 'How was this session?' })).toBeDefined()
  })

  test('the project facts are cut from the right in a narrow band', async ($, on) => {
    world(on)
    await $.session.start({ cwd: ROOT, surface: null, isInteractive: true } as any)
    await settle()
    const ui = await $.ui.mount({ plugin: 'project-os', surface: 'terminal', ...BAND })
    const facts = await ui.find({ type: 'Text', text: /FEAT-0157 doing/ })
    expect(facts!.props.wrap).toBe('truncate-end')
  })

  test('segments are taken out of the frozen tree beneath without changing it', () => {
    const seg = Object.freeze({ type: 'Box', props: { key: 'segment:x' }, children: [] })
    const engine = Object.freeze({ type: 'engine', ref: 1 })
    const tree = Object.freeze({ type: 'Box', props: {}, children: Object.freeze([engine, seg]) })
    const { segments, rest } = takeSegments(tree)
    expect(segments).toEqual([seg])
    expect((rest as any).children[0]).toBe(engine)
    expect((rest as any).children[1]).toEqual({ slot: true })
    expect(tree.children[1]).toBe(seg)
  })
})
