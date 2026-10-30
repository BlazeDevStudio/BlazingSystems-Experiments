'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../root/www/rental/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'operator dashboard script missing');

const elements = new Map();
const stored = new Map();
const alerts = [];
const requests = [];
let loseFirstResponse = true;
let loseFirstEnrollResponse = true;
const deviceId = '0123456789abcdef01234567';

function loadPage() {
const context = vm.createContext({
  document: {
    getElementById(id) {
      if (!elements.has(id)) {
        elements.set(id, { textContent: '', className: '', classList: { remove() {}, add() {} } });
      }
      return elements.get(id);
    },
  },
  location: { origin: 'http://r281.invalid' },
  sessionStorage: { getItem() { return null; }, setItem() {} },
  localStorage: {
    getItem(key) { return stored.get(key) ?? null; },
    setItem(key, value) { stored.set(key, value); },
    removeItem(key) { stored.delete(key); },
  },
  crypto: {
    getRandomValues(bytes) { bytes.forEach((_, i) => { bytes[i] = i + 1; }); return bytes; },
  },
  async fetch(_url, options) {
    const body = new URLSearchParams(options.body);
    requests.push(body);
    if (body.get('action') === 'add_time' && loseFirstResponse) {
      loseFirstResponse = false;
      throw Error('simulated lost response');
    }
    if (body.get('action') === 'enroll_create' && loseFirstEnrollResponse) {
      loseFirstEnrollResponse = false;
      throw Error('simulated lost enrollment response');
    }
    const response = body.get('action') === 'list'
      ? { ok: true, devices: [] }
      : body.get('action') === 'recent_events'
        ? { ok: true, events: [] }
        : body.get('action') === 'enroll_create'
          ? { ok: true, token: 'abcdef123456.0123456789abcdef0123456789abcdef0123', expires: 1900000000 }
          : { ok: true, lease_until: 1900000000 };
    return { async json() { return response; } };
  },
  alert(message) { alerts.push(message); },
  confirm() { return true; },
  URLSearchParams,
  Uint8Array,
  console,
});
vm.runInContext(script, context, { filename: 'rental-dashboard.js' });
return context;
}

function deferredEnrollmentPage() {
  const elements = new Map(), stored = new Map(), requests = [];
  let complete, fail, serial = 0;
  const context = vm.createContext({
    document: { getElementById(id) {
      if (!elements.has(id)) {
        let content = '';
        elements.set(id, { value: '', classList: { add() {}, remove() {} },
          get innerHTML() { return content; }, set innerHTML(value) { content = String(value); },
          get textContent() { return content; }, set textContent(value) { content = String(value); },
        });
      }
      return elements.get(id);
    } },
    location: { origin: 'https://r281.invalid' },
    sessionStorage: { getItem() { return null; } },
    localStorage: { getItem(key) { return stored.get(key) ?? null; },
      setItem(key, value) { stored.set(key, value); }, removeItem(key) { stored.delete(key); } },
    crypto: { getRandomValues(bytes) { bytes.fill(++serial); return bytes; } },
    URLSearchParams, Uint8Array,
    alert() {}, confirm() { return true; },
    fetch(url, options) {
      assert.equal(url, '/cgi-bin/rental-admin');
      assert.equal(options.method, 'POST');
      const body = new URLSearchParams(options.body);
      requests.push(body);
      if (body.get('action') === 'enroll_create') return new Promise((resolve, reject) => {
        complete = data => resolve({ async json() { return data; } });
        fail = reject;
      });
      assert.equal(body.get('action'), 'recent_events');
      return Promise.resolve({ async json() { return { ok: true, events: [] }; } });
    },
  });
  vm.runInContext(script, context, { filename: 'rental-dashboard.js' });
  context.document.getElementById('label').value = 'First phone';
  context.document.getElementById('ttl').value = '900';
  return { context, stored, requests, output: context.document.getElementById('enrollOut'),
    finish(outcome) {
      if (outcome === 'lost') fail(Error('simulated response loss'));
      else complete(outcome === 'success'
        ? { ok: true, token: 'aaaaaaaaaaaa.111111111111111111111111111111111111', expires: 1900000000 }
        : { ok: false, error: 'fixture refusal' });
    } };
}

async function enrollmentResponseCases() {
  const checks = [];
  for (const outcome of ['success', 'refused', 'lost']) {
    checks.push(['current request ' + outcome, async () => {
      const p = deferredEnrollmentPage(), work = p.context.enroll(), id = p.context.pendingEnrollment().request_id;
      p.finish(outcome); await work;
      assert.equal(p.context.pendingEnrollment().request_id, id, 'retain the same nonsecret request for inspection/retry');
      assert.ok(p.output.textContent.includes(outcome === 'success' ? 'aaaaaaaaaaaa.' : outcome === 'refused' ? 'fixture refusal' : 'uncertain'));
      assert.equal(p.requests.filter(r => r.get('action') === 'enroll_create').length, 1);
      assert.equal(p.requests[0].get('request_id'), id);
    }]);
    for (const state of ['replaced', 'cleared', 'invalid']) checks.push([state + ' request ignores delayed ' + outcome, async () => {
      const p = deferredEnrollmentPage(), work = p.context.enroll();
      if (state === 'replaced') p.stored.set('blazeRentalPendingEnrollV1', JSON.stringify({ request_id: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', label: 'Second phone', ttl: '900' }));
      else if (state === 'cleared') p.stored.clear();
      else p.stored.set('blazeRentalPendingEnrollV1', '{damaged');
      p.output.textContent = 'Newer view';
      const current = p.stored.get('blazeRentalPendingEnrollV1');
      p.finish(outcome); await work;
      assert.equal(p.output.textContent, 'Newer view', 'obsolete result must not replace the current provisioning view');
      assert.equal(p.stored.get('blazeRentalPendingEnrollV1'), current, 'obsolete result must not alter current pending storage');
    }]);
  }
  checks.push(['confirmed clear and new enrollment ignore first result and allow retry', async () => {
    const p = deferredEnrollmentPage(), first = p.context.enroll(), firstId = p.context.pendingEnrollment().request_id;
    p.context.clearPendingEnroll();
    p.context.document.getElementById('label').value = 'Second phone';
    await p.context.enroll();
    const nextId = p.context.pendingEnrollment().request_id;
    assert.notEqual(nextId, firstId);
    p.finish('success'); await first;
    assert.equal(p.output.textContent, '', 'old token must not be displayed under the second pending request');
    const retry = p.context.retryPendingEnroll();
    p.finish('success'); await retry;
    const enrolls = p.requests.filter(r => r.get('action') === 'enroll_create');
    assert.equal(enrolls.length, 2, 'busy state must release so the retained second request can be sent');
    assert.equal(enrolls[1].get('request_id'), nextId);
    assert.equal(p.context.pendingEnrollment().request_id, nextId);
    assert.ok(p.output.textContent.includes('aaaaaaaaaaaa.'));
  }]);
  checks.push(['retry removes obsolete provisioning output while transport is pending', async () => {
    const p = deferredEnrollmentPage(); p.output.textContent = 'Old token output';
    const work = p.context.enroll();
    const duringRequest = p.output.textContent;
    p.finish('success'); await work;
    assert.equal(duringRequest, '', 'previous provisioning output must be cleared before awaiting a new result');
  }]);
  let failed = 0;
  for (const [name, check] of checks) {
    try { await check(); console.log('PASS: ' + name); }
    catch (error) { failed++; console.error('FAIL: ' + name + ': ' + error.message); }
  }
  console.log('Enrollment response association: ' + (checks.length - failed) + '/' + checks.length + ' passed');
  assert.equal(failed, 0, 'enrollment responses must belong to the current pending request');
}

(async () => {
  const firstPage = loadPage();
  await firstPage.paid('add_time', { device_id: deviceId, seconds: 600 });
  const pending = [...stored.values()].map(value => JSON.parse(value));
  assert.equal(pending.length, 1, 'lost response must retain one pending operation');
  assert.match(pending[0].request_id, /^[0-9a-f]{32}$/);
  assert.equal(pending[0].data.device_id, deviceId);
  assert.ok(alerts.some(message => message.includes('uncertain')));
  assert.ok(!JSON.stringify(pending[0]).includes('admin_token'), 'no admin token in durable browser state');

  const reloadedPage = loadPage();
  assert.equal(reloadedPage.pendingOperation().request_id, pending[0].request_id);
  await reloadedPage.retryPending();
  const grants = requests.filter(body => body.get('action') === 'add_time');
  assert.equal(grants.length, 2, 'must retry the same operation once');
  assert.equal(grants[0].get('request_id'), grants[1].get('request_id'));
  assert.equal(stored.size, 0, 'positive replay acknowledgment clears pending operation');
  firstPage.document.getElementById('label').value = 'Test phone';
  firstPage.document.getElementById('ttl').value = '900';
  await firstPage.enroll();
  const enrollmentPending = [...stored.values()].map(value => JSON.parse(value));
  assert.equal(enrollmentPending.length, 1, 'lost enrollment response must retain one pending request');
  assert.match(enrollmentPending[0].request_id, /^[0-9a-f]{32}$/);
  assert.ok(!JSON.stringify(enrollmentPending[0]).includes('abcdef123456.'), 'browser must not store enrollment secret');
  const enrollmentReload = loadPage();
  await enrollmentReload.retryPendingEnroll();
  const enrolls = requests.filter(body => body.get('action') === 'enroll_create');
  assert.equal(enrolls.length, 2, 'reload must retry one enrollment request');
  assert.equal(enrolls[0].get('request_id'), enrolls[1].get('request_id'));
  assert.equal(stored.size, 1, 'pending ID remains until token is copied or inspected');
  enrollmentReload.clearPendingEnroll();
  assert.equal(stored.size, 0, 'operator confirmation clears pending enrollment');
  await enrollmentResponseCases();
  console.log('R281 admin lost-response pending request contract PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
