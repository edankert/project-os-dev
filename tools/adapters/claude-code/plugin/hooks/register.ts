// project-os plugin for Claude Code (project-os-dev FEAT-0041).
//
// Every project-os repo loads this module in every Claude Code session, inside
// a cockpit terminal or not. The template sync places this folder and
// generate-adapters.py registers it in the repo's .claude/settings.json, as a
// marketplace that lives in the repo (tools/adapters/claude-code/ADAPTER.md,
// "The project-os plugin"). Claude Code runs it from this folder, so a sync
// that changes it changes what runs at the next session.
//
// It does three things the shell hooks cannot:
//
//   * A file changed from the shell counts as a write at close-out (HC-006,
//     TASK-0200). The close-out check is told a session wrote something by a
//     marker that only the Edit, Write and NotebookEdit tools leave. This
//     module fingerprints the working tree when a main-loop turn starts and
//     again when it stops, and leaves the same marker when the two differ.
//   * A session on the wrong model is named (HC-011, TASK-0201). A resumed
//     session keeps the model its transcript was saved with, whatever the
//     repo pins; a warning row above the prompt and a context block say so.
//   * The project line above the prompt (HC-012, TASK-0202): the focus item,
//     its status and phase, the validator's counts and the routing hint.
//     Another plugin may add its facts to the end of the same line; the rules
//     are in ADAPTER.md, "The project line".
//
// Everything is read from the repo's own scripts, in the background, and kept
// in memory; drawing never runs a script. A script that fails leaves its fact
// out of the line. Nothing here ever blocks or slows a turn.

import type { EngineInterface, Register } from 'claude-code'

/** What one script run gave, or undefined when it could not run at all. */
type Ran = { exitCode: number; stdout: string; stderr: string }

async function run(
  $: EngineInterface, argv: string[], cwd: string, init: { stdin?: string; env?: Record<string, string>; timeoutMs?: number } = {},
): Promise<Ran | undefined> {
  try {
    return await $.process.run(argv, { cwd, ...init })
  } catch {
    return undefined
  }
}

/** The template folder this plugin sits in: tools/adapters/claude-code. */
const adapterDir = ($: EngineInterface): string => $.plugin.root.replace(/\/plugin\/?$/, '')

// ---------------------------------------------------------------------------
// A file changed from the shell counts as a write (HC-006, TASK-0200)

/** Two digests of the working tree: everything, and the part the line reads
 *  (SNAPSHOT.yaml and docs/). `git status` alone would miss a file that was
 *  already modified and is modified again, so the diff's digest is added. A
 *  path changed and changed back within one turn is not caught; the check is
 *  about a file left changed. Exit 3 means "not a git repository". */
const FINGERPRINT = [
  'git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 3',
  'all=$( { git status --porcelain=v1 -z; git diff HEAD --no-ext-diff 2>/dev/null; } | cksum )',
  'docs=$( { git status --porcelain=v1 -z -- SNAPSHOT.yaml docs; git diff HEAD --no-ext-diff -- SNAPSHOT.yaml docs 2>/dev/null; } | cksum )',
  'printf \'%s\\n%s\\n\' "$all" "$docs"',
].join('\n')

export type Fingerprint = { all: string; docs: string }

/** The two digests from FINGERPRINT's output, or undefined when it failed. */
export function parseFingerprint(r: Ran | undefined): Fingerprint | undefined {
  if (!r || r.exitCode !== 0) return undefined
  const [all, docs] = r.stdout.split('\n')
  return all && docs ? { all, docs } : undefined
}

async function fingerprint($: EngineInterface): Promise<Fingerprint | undefined> {
  return parseFingerprint(await run($, ['bash', '-c', FINGERPRINT], await $.session.root()))
}

/** Leave the marker session-touch.sh leaves, at the path shared/session-marker.sh
 *  gives, so the rule for the path stays in one place. close-out-check.sh keys
 *  it on $CLAUDE_PROJECT_DIR; the session's root stands in when that is unset. */
const WRITE_MARKER = '. "$1" || exit 1; m=$(session_marker "$2" "${CLAUDE_PROJECT_DIR:-$3}") || exit 1; : > "$m"'

async function writeMarker($: EngineInterface, sessionId: string): Promise<void> {
  const root = await $.session.root()
  await run($, ['bash', '-c', WRITE_MARKER, 'project-os', `${adapterDir($)}/hooks/shared/session-marker.sh`, sessionId, root], root)
}

// ---------------------------------------------------------------------------
// The session runs on the pinned model (HC-011, TASK-0201)

/** One spelling for a model name: lower case, no `claude-` prefix, no date or
 *  context suffix. `$.session.model()` gives the name as /model shows it, and
 *  the pin may be a full ID; both become e.g. `opus-5-5`. */
export function modelKey(name: string): string {
  return name.trim().toLowerCase()
    .replace(/\[[^\]]*\]$/, '')
    .replace(/^claude[- ]/, '')
    .replace(/[ .]/g, '-')
    .replace(/-\d{8}$/, '')
}

/** Whether a session's model honours the pin. A pin that names only a family
 *  (`opus`, `sonnet`) is honoured by any model of that family. */
export function honoursPin(model: string, pin: string): boolean {
  const m = modelKey(model)
  const p = modelKey(pin)
  if (!m || !p) return true
  if (m === p) return true
  return /^[a-z]+$/.test(p) && m.split('-')[0] === p
}

export function wrongModelSentence(model: string, pin: string): string {
  return `This session runs ${model}; this repo pins ${pin} (.claude/settings.json). Switch with /model, or start a new session.`
}

/** The repo's pin, or undefined when there is none or the file cannot be read. */
async function pinnedModel($: EngineInterface): Promise<string | undefined> {
  try {
    const text = String(await $.fs.read(`${await $.session.root()}/.claude/settings.json`))
    const pin = (JSON.parse(text) as { model?: unknown }).model
    return typeof pin === 'string' && pin.trim() ? pin.trim() : undefined
  } catch {
    return undefined
  }
}

async function modelWarning($: EngineInterface): Promise<string | undefined> {
  const pin = await pinnedModel($)
  if (!pin) return undefined
  try {
    const model = await $.session.model()
    return honoursPin(model, pin) ? undefined : wrongModelSentence(model, pin)
  } catch {
    return undefined
  }
}

// ---------------------------------------------------------------------------
// The project line (HC-012, TASK-0202)

export type Focus = { id: string; status: string; phase?: string } | 'none'

/** The facts on the line; a fact not read yet, or whose script failed, is absent. */
export type Facts = { focus?: Focus; route?: string; errors?: number; reviewStale?: number }

/** What the routing hint's category in brackets is called on the line. */
const ROUTES: Record<string, string> = {
  'planning': 'planner',
  'execution': 'implement here',
  'review': 'independent-reviewer',
  'parked, not terminal': 'parked',
  'terminal': 'nothing in flight',
}

/** The focus and route from model-routing-hint.sh's line, which states the
 *  focus item, its status and phase, and in brackets what kind of work it is.
 *  Read from the hint rather than SNAPSHOT.yaml so the line and the hint the
 *  model gets can never disagree. */
export function parseHint(text: string): Pick<Facts, 'focus' | 'route'> {
  const line = text.split('\n').find(l => l.startsWith('project-os: ')) ?? ''
  if (!line) return {}
  if (line.startsWith('project-os: no focus item')) return { focus: 'none' }
  const m = /^project-os: focus item (\S+) is '([^']*)'(?:, phase (\S+))? \(([^)]*)\)/.exec(line)
  if (!m || !m[1]) return {}
  const focus: Focus = { id: m[1], status: m[2] ?? '' }
  if (m[3]) focus.phase = m[3]
  const route = ROUTES[m[4] ?? '']
  return route ? { focus, route } : { focus }
}

/** The validator's counts from its output, or undefined when it did not finish:
 *  only a run that printed its own verdict line is counted. */
export function parseValidator(r: Ran | undefined): Pick<Facts, 'errors' | 'reviewStale'> | undefined {
  if (!r) return undefined
  const out = `${r.stdout}\n${r.stderr}`
  if (!/^validate-docs: (OK|FAIL)\b/m.test(out)) return undefined
  const lines = out.split('\n')
  return {
    errors: lines.filter(l => /^ERROR\b/.test(l)).length,
    reviewStale: lines.filter(l => l.includes('[REVIEW-STALE]')).length,
  }
}

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`

/** The line's text: project facts only, in order, joined by ` · `. */
export function lineText(f: Facts): string {
  const parts: string[] = []
  if (f.focus === 'none') parts.push('no focus item')
  else if (f.focus) {
    parts.push(f.focus.status ? `${f.focus.id} ${f.focus.status}` : f.focus.id)
    if (f.focus.phase) parts.push(f.focus.phase)
  }
  if (f.errors !== undefined) parts.push(plural(f.errors, 'validator error', 'validator errors'))
  if (f.reviewStale !== undefined) parts.push(`${f.reviewStale} review-stale`)
  if (f.route) parts.push(`route: ${f.route}`)
  return parts.join(' · ')
}

/** The keys the line contract names. */
export const LINE_KEY = 'project-os:line'
const SEGMENT = /^segment:/

type Node = { type?: string; props?: Record<string, unknown>; children?: unknown[] }

/** Splits the tree beneath into the segments it holds and the rest. The tree
 *  from next(e) is frozen, so the rest is rebuilt from copies; every other
 *  node, the engine's own included, is kept where it was. `slot` marks where
 *  the first segment stood, so the line can be put back in its place. */
export function takeSegments(tree: unknown): { segments: unknown[]; rest: unknown } {
  const segments: unknown[] = []
  const SLOT = { slot: true }
  const walk = (t: unknown): unknown => {
    if (!t || typeof t !== 'object') return t
    const n = t as Node
    if (typeof n.props?.key === 'string' && SEGMENT.test(n.props.key)) {
      segments.push(t)
      return segments.length === 1 ? SLOT : undefined
    }
    if (!Array.isArray(n.children)) return t
    return { ...n, children: n.children.map(walk).filter(c => c !== undefined) }
  }
  return { segments, rest: walk(tree) }
}

/** Puts `node` where the first segment stood (see takeSegments). */
function fillSlot(tree: unknown, node: unknown): unknown {
  if (!tree || typeof tree !== 'object') return tree
  if ((tree as { slot?: boolean }).slot === true) return node
  const n = tree as Node
  return Array.isArray(n.children) ? { ...n, children: n.children.map(c => fillSlot(c, node)) } : tree
}

// ---------------------------------------------------------------------------

/** The line's facts and the module's other state; one Claude session per load. */
const facts: Facts = {}
const st: {
  before?: Promise<Fingerprint | undefined>
  warning?: string
  refreshing?: boolean
  again?: boolean
  started?: boolean
} = {}

/** Re-reads the line's facts, one refresh at a time; a request that arrives
 *  while one runs makes it run once more. Never awaited by a hook. */
function refresh($: EngineInterface): void {
  st.started = true
  if (st.refreshing) { st.again = true; return }
  st.refreshing = true
  void refreshLoop($).catch(() => undefined).finally(() => { st.refreshing = false })
}

async function refreshLoop($: EngineInterface): Promise<void> {
  do {
    st.again = false
    const root = await $.session.root()
    const hint = await run($, ['bash', `${adapterDir($)}/hooks/model-routing-hint.sh`], root,
      { stdin: '{}', env: { CLAUDE_PROJECT_DIR: root } })
    const read = hint && hint.exitCode === 0 ? parseHint(hint.stdout) : {}
    facts.focus = read.focus
    facts.route = read.route
    $.ui.invalidate('ui.render')
    const counts = parseValidator(await run($, ['bash', 'tools/scripts/validate-docs.sh'], root, { timeoutMs: 300_000 }))
    // A run that did not finish keeps the last counts it had.
    if (counts) Object.assign(facts, counts)
    $.ui.invalidate('ui.render')
  } while (st.again)
}

/** Redraws when the wrong-model warning appears or goes away. */
async function checkModel($: EngineInterface): Promise<void> {
  const warning = await modelWarning($)
  if (warning !== st.warning) {
    st.warning = warning
    $.ui.invalidate('ui.render')
  }
}

export const register: Register = on => {
  on('session.start', ($, e, next) => {
    refresh($)
    void checkModel($).catch(() => undefined)
    return next(e)
  })

  on('turn.start', ($, e, next) => {
    // A subagent's turn runs inside the main loop's.
    if (e.agentId === undefined) {
      st.before = fingerprint($).catch(() => undefined)
      void checkModel($).catch(() => undefined)
    }
    return next(e)
  })

  // Before the settings Stop hooks run (close-out-check.sh among them), so the
  // marker is there when the check looks for it.
  on('classic.Stop', async ($, e, next) => {
    try {
      const before = await st.before
      const after = before ? await fingerprint($) : undefined
      // A blocked stop continues the same turn: compare its next stop with now.
      st.before = after ? Promise.resolve(after) : undefined
      if (before && after) {
        const sessionId = (e as { session_id?: unknown }).session_id
        if (after.all !== before.all && typeof sessionId === 'string' && sessionId) await writeMarker($, sessionId)
        if (after.docs !== before.docs) refresh($)
      }
    } catch {
      // Whatever failed, the turn ends as it would have without this module.
    }
    return next(e)
  })

  // The wrong-model sentence in the model's own context, for a surface that
  // draws nothing (VS Code, `claude -p`).
  on('prompt.context', async ($, e, next) => {
    const r = await next(e)
    const warning = await modelWarning($).catch(() => undefined)
    return warning ? { ...r, blocks: [...r.blocks, { name: 'projectOsModel', text: warning }] } : r
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const beneath = await next(e)
    if (e.props.hasSurvey) return beneath
    // A plugin reloaded mid-session hears no session.start.
    if (!st.started) refresh($)
    const { Box, Text } = $.ui.resolve(e)
    const text = lineText(facts)
    const { segments, rest } = takeSegments(beneath)
    const line = h(Box, { key: LINE_KEY, flexDirection: 'row' },
      text ? h(Text, { wrap: 'truncate-end' }, text) : null,
      ...segments)
    const block = st.warning
      ? h(Box, { flexDirection: 'column' }, h(Text, { color: 'warning', wrap: 'wrap' }, st.warning), line)
      : line
    if (segments.length) return fillSlot(rest, block) as typeof beneath
    return h(Box, { flexDirection: 'column' }, rest, block) as typeof beneath
  })
}
