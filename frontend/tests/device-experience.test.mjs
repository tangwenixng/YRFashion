import assert from 'node:assert/strict'
import test from 'node:test'

import {
  detectRouteExperience,
  resolveAdminExperience,
  resolveAdminHomeRoute,
  resolveAdminLoginRoute,
  resolvePathForExperience,
} from '../src/router/deviceExperience.ts'

const iphoneUA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
const androidUA =
  'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36'
const desktopUA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'

test('resolveAdminExperience uses mobile heuristics only in auto mode', () => {
  assert.equal(resolveAdminExperience({ userAgent: iphoneUA, override: 'auto' }), 'mobile')
  assert.equal(resolveAdminExperience({ userAgent: androidUA, override: 'auto' }), 'mobile')
  assert.equal(resolveAdminExperience({ userAgent: desktopUA, override: 'auto' }), 'desktop')
})

test('resolveAdminExperience honors manual overrides ahead of user agent detection', () => {
  assert.equal(resolveAdminExperience({ userAgent: desktopUA, override: 'force-mobile' }), 'mobile')
  assert.equal(resolveAdminExperience({ userAgent: iphoneUA, override: 'force-desktop' }), 'desktop')
})

test('mobile and desktop experiences resolve to separate login and home routes', () => {
  assert.equal(resolveAdminLoginRoute('mobile'), '/m/login')
  assert.equal(resolveAdminLoginRoute('desktop'), '/login')
  assert.equal(resolveAdminHomeRoute('mobile'), '/m/home')
  assert.equal(resolveAdminHomeRoute('desktop'), '/dashboard')
})

test('detectRouteExperience treats /login as neutral and /m/* as explicit mobile', () => {
  assert.equal(detectRouteExperience('/'), null)
  assert.equal(detectRouteExperience('/login'), null)
  assert.equal(detectRouteExperience('/m/login'), 'mobile')
  assert.equal(detectRouteExperience('/m/products/2/edit'), 'mobile')
  assert.equal(detectRouteExperience('/products'), 'desktop')
})

test('resolvePathForExperience maps explicit routes between mobile and desktop families', () => {
  assert.equal(resolvePathForExperience('/login', 'mobile'), '/m/login')
  assert.equal(resolvePathForExperience('/dashboard', 'mobile'), '/m/home')
  assert.equal(resolvePathForExperience('/products/12/edit', 'mobile'), '/m/products/12/edit')
  assert.equal(resolvePathForExperience('/m/home', 'desktop'), '/dashboard')
  assert.equal(resolvePathForExperience('/m/products/12/images', 'desktop'), '/products/12/edit')
  assert.equal(resolvePathForExperience('/m/messages/18', 'desktop'), '/messages')
})
