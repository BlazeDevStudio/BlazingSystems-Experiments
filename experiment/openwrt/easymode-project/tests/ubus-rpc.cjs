// Exercise the shipped inline page with a fake DOM/transport; never contact a router.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../installers/offline-html/EasyMode-Installer.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(script, 'inline installer script is present');

async function testPage(input, expected, failure = '') {
  const nodes = Object.fromEntries(['url', 'user', 'pass', 'bar', 'log', 'test', 'install'].map(id => [id, {}]));
  Object.assign(nodes.url, { value: input });
  Object.assign(nodes.user, { value: 'fixture-user' });
  Object.assign(nodes.pass, { value: 'fixture-only' });
  Object.assign(nodes.log, { textContent: 'Ready.' });
  Object.assign(nodes.install, { disabled: true });
  const requests = [];
  const context = vm.createContext({
    document: { getElementById: id => nodes[id] },
    fetch: async (url, options) => {
      requests.push({ url, options });
      return {
        ok: failure !== 'http', status: failure === 'http' ? 503 : 200,
        json: async () => ({ result: [0, requests.length === 1
          ? { ubus_rpc_session: failure === 'login' ? '' : 'fixture-session' }
          : { model: 'fixture-model' }] })
      };
    }
  });
  vm.runInContext(script[1], context, { timeout: 1000 });
  await nodes.test.onclick();
  if (expected === null) {
    assert.equal(requests.length, 0, 'blank URL must not reach transport');
  } else {
    const count = failure ? 1 : 2;
    assert.deepEqual(requests.map(r => r.url), Array(count).fill(expected), input);
    for (const request of requests) {
      assert.equal(request.options.method, 'POST');
      assert.equal(request.options.headers['Content-Type'], 'application/json');
    }
    assert.deepEqual(JSON.parse(requests[0].options.body), {
      jsonrpc: '2.0', id: 1, method: 'call',
      params: ['00000000000000000000000000000000', 'session', 'login', {
        username: 'fixture-user', password: 'fixture-only'
      }]
    });
    if (!failure) assert.deepEqual(JSON.parse(requests[1].options.body).params,
      ['fixture-session', 'system', 'board', {}]);
  }
  if (failure || expected === null) {
    assert.equal(nodes.bar.value, 0);
    assert.equal(nodes.install.disabled, true);
    assert.match(nodes.log.textContent, /Connection failed:/);
    if (failure === 'http') assert.match(nodes.log.textContent, /HTTP 503/);
    if (failure === 'login') assert.match(nodes.log.textContent, /Login failed/);
    if (expected === null) assert.match(nodes.log.textContent, /Router URL is empty/);
  } else {
    assert.equal(nodes.bar.value, 100);
    assert.equal(nodes.install.disabled, false);
    assert.match(nodes.log.textContent, /Connection test passed\./);
  }
}

(async () => {
  const cases = [
    ['http://192.0.2.1', 'http://192.0.2.1/ubus'],
    ['http://192.0.2.1/', 'http://192.0.2.1/ubus'],
    ['http://192.0.2.1/ubus', 'http://192.0.2.1/ubus'],
    ['http://192.0.2.1/ubus/', 'http://192.0.2.1/ubus'],
    ['  http://192.0.2.1  ', 'http://192.0.2.1/ubus'],
    ['https://router.example.invalid:8443', 'https://router.example.invalid:8443/ubus'],
    ['http://[2001:db8::1]:8080/', 'http://[2001:db8::1]:8080/ubus'],
    ['http://192.0.2.1///', 'http://192.0.2.1/ubus'],
    ['https://router.example.invalid/prefix/ubus/', 'https://router.example.invalid/prefix/ubus']
  ];
  for (const [input, expected] of cases) await testPage(input, expected);
  await testPage('  ', null);
  await testPage('http://192.0.2.1/ubus', 'http://192.0.2.1/ubus', 'http');
  await testPage('http://192.0.2.1/ubus', 'http://192.0.2.1/ubus', 'login');
  console.log('ubus RPC page passed: 12 cases, no network');
})().catch(error => { console.error(error); process.exitCode = 1; });
