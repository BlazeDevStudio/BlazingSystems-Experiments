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
const deviceId = '0123456789abcdef01234567';

function loadPage() {
const context = vm.createContext({
  document: {
    getElementById(id) {
      if (!elements.has(id)) {
        elements.set(id, { textContent: '', className: '', classList: { remove() {} } });
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
    const response = body.get('action') === 'list'
      ? { ok: true, devices: [] }
      : body.get('action') === 'recent_events'
        ? { ok: true, events: [] }
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
  console.log('R281 admin lost-response pending request contract PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
