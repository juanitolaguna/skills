import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'

const MENU = { plugin: 'open-local', surface: 'desktop', component: 'ContextMenu' } as const
const CWD = '/Users/me/dev/proj'

type Call = { argv: readonly string[]; cwd?: string }

function stub(on: On, calls: Call[]) {
  on('session.cwd', () => ({ value: CWD }))
  on('ui.toast', () => ({ value: undefined }))
  on('process.run', (_, e) => {
    calls.push({ argv: e.argv, cwd: e.init?.cwd })
    return { value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
}

test('right-click menu rows run subl . and open . in the project folder', async ($, on) => {
  const calls: Call[] = []
  stub(on, calls)

  const ui = await $.ui.mount({ ...MENU, props: {} })
  await ui.press({ key: 'subl' })
  await ui.press({ key: 'finder' })
  await ui.unmount()

  expect(calls).toEqual([
    { argv: ['/bin/bash', '-lc', 'subl .'], cwd: CWD },
    { argv: ['/bin/bash', '-lc', 'open .'], cwd: CWD },
  ])
})

test('/finder runs open . and reports it', async ($, on) => {
  const calls: Call[] = []
  stub(on, calls)

  const { text } = await $.command.run({
    command: 'finder',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 80 },
  })

  expect(calls).toEqual([{ argv: ['/bin/bash', '-lc', 'open .'], cwd: CWD }])
  expect(text).toBe(`Opened in Finder: ${CWD}`)
})

