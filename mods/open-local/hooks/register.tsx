import type { EngineInterface, Register } from 'claude-code'

// Each action is a bash one-liner run in the session's folder
const ACTIONS = {
  subl: { script: 'subl .', label: 'Open project in Sublime', done: 'Opened in Sublime' },
  finder: { script: 'open .', label: 'Open project in Finder', done: 'Opened in Finder' },
} as const
type Action = keyof typeof ACTIONS

async function runAction($: EngineInterface, action: Action): Promise<string> {
  const cwd = await $.session.cwd()
  const { script, done } = ACTIONS[action]
  // -l so the login profile puts /usr/local/bin (subl) on PATH
  const { exitCode, stdout, stderr } = await $.process.run(['/bin/bash', '-lc', script], { cwd, timeoutMs: 10_000 })
  const msg = exitCode === 0 ? `${done}: ${stdout.trim() || cwd}` : `\`${script}\` failed (${exitCode}): ${stderr.trim()}`
  $.ui.toast(msg)
  return msg
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({ name: 'subl', description: 'Open the current project in Sublime Text' })
    await $.command.register({ name: 'finder', description: 'Open the current project in Finder' })
    return started
  })

  on('command.run', { command: 'subl' }, async $ => ({ text: await runAction($, 'subl'), isTextDisplayOnly: true }))
  on('command.run', { command: 'finder' }, async $ => ({ text: await runAction($, 'finder'), isTextDisplayOnly: true }))

  // Right-click anywhere in the transcript (desktop app)
  on('ui.render', { component: 'ContextMenu' }, ($, e) => {
    const { Box, Button } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Button key="subl" onPress={() => void runAction($, 'subl')}>{ACTIONS.subl.label}</Button>
        <Button key="finder" onPress={() => void runAction($, 'finder')}>{ACTIONS.finder.label}</Button>
      </Box>
    )
  })
}
