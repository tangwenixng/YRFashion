import assert from 'node:assert/strict'
import test from 'node:test'

import { resolveAdminBasePath } from '../src/router/base.ts'

test('resolveAdminBasePath keeps root-mounted desktop routes on /', () => {
  assert.equal(resolveAdminBasePath('/login'), '/')
  assert.equal(resolveAdminBasePath('/dashboard'), '/')
  assert.equal(resolveAdminBasePath('/products'), '/')
})

test('resolveAdminBasePath strips hidden prefixes for desktop routes', () => {
  assert.equal(resolveAdminBasePath('/gate/login'), '/gate/')
  assert.equal(resolveAdminBasePath('/gate/products'), '/gate/')
  assert.equal(resolveAdminBasePath('/yr-admin/messages'), '/yr-admin/')
})

test('resolveAdminBasePath treats /m as a route namespace, not part of the history base', () => {
  assert.equal(resolveAdminBasePath('/m/login'), '/')
  assert.equal(resolveAdminBasePath('/m/products'), '/')
  assert.equal(resolveAdminBasePath('/gate/m/login'), '/gate/')
  assert.equal(resolveAdminBasePath('/gate/m/products'), '/gate/')
  assert.equal(resolveAdminBasePath('/hidden/prefix/m/home'), '/hidden/prefix/')
})
