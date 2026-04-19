import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const testDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(testDir, '..')

const readEntrypointEnv = (entryPath) => {
  const output = execFileSync(
    'sh',
    [
      '-lc',
      '. ./docker-entrypoint.d/10-admin-entry.envsh; printf "%s\\0%s\\0%s\\0%s\\0%s" "$ADMIN_ENTRY_PATH" "$ADMIN_ENTRY_PATH_REDIRECT_SOURCE" "$ADMIN_ENTRY_LOCATION_BLOCK" "$ADMIN_SCOPED_STATIC_LOCATION_BLOCK" "$ROOT_LOCATION_TRY_FILES_ARGS"',
    ],
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        ADMIN_ENTRY_PATH: entryPath,
      },
      encoding: 'utf8',
    },
  )

  const [
    normalizedEntryPath,
    redirectSource,
    entryLocationBlock,
    scopedStaticLocationBlock,
    rootLocationTryFilesArgs,
  ] = output.split('\0')

  return {
    normalizedEntryPath,
    redirectSource,
    entryLocationBlock,
    scopedStaticLocationBlock,
    rootLocationTryFilesArgs,
  }
}

test('root-mounted admin keeps SPA fallback and rewrites nested relative assets', () => {
  const env = readEntrypointEnv('/')

  assert.equal(env.normalizedEntryPath, '/')
  assert.equal(env.redirectSource, '/__admin-entry-disabled__')
  assert.equal(env.entryLocationBlock, '')
  assert.equal(env.rootLocationTryFilesArgs, '$uri $uri/ /index.html')
  assert.match(env.scopedStaticLocationBlock, /\(\?:\.\+\/\)\?assets\/\(\.\+\)\$/)
  assert.match(env.scopedStaticLocationBlock, /\/assets\/\$1 break;/)
  assert.ok(env.scopedStaticLocationBlock.includes('favicon\\.svg'))
})

test('subpath-mounted admin rewrites nested assets before SPA fallback', () => {
  const env = readEntrypointEnv('/fashion-dev')

  assert.equal(env.normalizedEntryPath, '/fashion-dev/')
  assert.equal(env.redirectSource, '/fashion-dev')
  assert.equal(env.rootLocationTryFilesArgs, '$uri =404')
  assert.match(env.entryLocationBlock, /location \/fashion-dev\/ \{/)
  assert.doesNotMatch(env.entryLocationBlock, /\^~/)
  assert.match(env.scopedStaticLocationBlock, /location ~ \^\/fashion-dev\/\(\?:\.\+\/\)\?assets\/\(\.\+\)\$ \{/)
  assert.match(env.scopedStaticLocationBlock, /\/assets\/\$1 break;/)
  assert.ok(env.scopedStaticLocationBlock.includes('location ~ ^/fashion-dev/(?:.+/)?favicon\\.svg$'))
})
