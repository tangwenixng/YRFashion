import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(scriptDir, '..')

const resolveBuildTime = () => {
  const injectedBuildTime = process.env.VITE_APP_BUILD_TIME?.trim()
  if (injectedBuildTime) {
    return injectedBuildTime
  }

  try {
    return execFileSync('git', ['log', '-1', '--format=%cI'], {
      cwd: projectRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
  } catch {
    return 'unknown'
  }
}

const viteBinPath = path.join(projectRoot, 'node_modules', 'vite', 'bin', 'vite.js')
const buildTime = resolveBuildTime()
const viteArgs = process.argv.slice(2)

console.log(`[build] VITE_APP_BUILD_TIME=${buildTime}`)

execFileSync(process.execPath, [viteBinPath, 'build', ...viteArgs], {
  cwd: projectRoot,
  env: {
    ...process.env,
    VITE_APP_BUILD_TIME: buildTime,
  },
  stdio: 'inherit',
})
