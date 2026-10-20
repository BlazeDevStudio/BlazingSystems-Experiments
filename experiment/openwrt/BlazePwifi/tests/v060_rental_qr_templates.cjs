// Run the real offline template scripts and bundled QR renderer in a Node VM.
// Only the three DOM output properties and form inputs need a browser stub.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const root = path.join(__dirname, '..');
const qrSource = fs.readFileSync(path.join(root, 'ui/vendor/qrcode/qrcode.js'), 'utf8');

function element(value = '') {
  let html = '', text = '';
  return {
    value,
    get innerHTML() { return html; },
    set innerHTML(value) { html = String(value); text = html.replace(/<[^>]*>/g, ''); },
    get textContent() { return text; },
    set textContent(value) { text = String(value); html = text; }
  };
}

function loadTemplate(filename) {
  const source = fs.readFileSync(path.join(root, 'tools', filename), 'utf8');
  const nodes = new Map();
  for (const match of source.matchAll(/<(?:input|select|div|pre)\b[^>]*\bid="([^"]+)"[^>]*>/g)) {
    nodes.set(match[1], element(match[0].match(/\bvalue="([^"]*)"/)?.[1] || ''));
  }
  const context = vm.createContext({document: {getElementById: id => nodes.get(id)}});
  for (const match of source.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(match[1].replace('__QRCODE_JS__', () => qrSource), context, {timeout: 3000});
  }
  nodes.get('token').value = 'fixture-token.one-time';
  return {generate: () => context.generateQr(), get: id => nodes.get(id)};
}

const templates = [
  ['binding', 'BlazeRental-Binding-QR.template.html'],
  ['Device Owner', 'BlazeRental-QR-Setup.template.html']
];
const invalidInputs = [
  ['invalid server', 'server', 'invalid'],
  ['missing server', 'server', ''],
  ['missing token', 'token', ''],
  ['invalid certificate pin', 'certPin', 'not-a-sha256']
];

for (const [label, filename] of templates) {
  const cases = label === 'binding'
    ? [...invalidInputs, ['invalid token format', 'token', 'missing-separator']]
    : invalidInputs;
  for (const [failure, field, invalidValue] of cases) {
    test(`${label}: ${failure} retry removes the previous QR, JSON and success state`, () => {
      const tool = loadTemplate(filename);
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/, 'valid input must generate a real QR');
      assert.match(tool.get('state').textContent, /QR ready/);
      const payload = JSON.parse(tool.get('json').textContent);
      const binding = payload['android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE'] || payload;
      assert.equal(binding.server_url, 'https://192.168.1.1:8443');
      assert.equal(binding.enrollment_token, 'fixture-token.one-time');

      const originalValue = tool.get(field).value;
      tool.get(field).value = invalidValue;
      tool.generate();
      assert.equal(tool.get('qr').innerHTML.length, 0, 'failed retry leaves a scannable old QR');
      assert.equal(tool.get('json').textContent, '', 'failed retry leaves reusable old enrollment JSON');
      assert.notEqual(tool.get('state').textContent, '', 'validation error must remain visible');
      assert.doesNotMatch(tool.get('state').innerHTML, /class="ok"|QR ready/, 'failed retry still claims success');

      tool.get(field).value = originalValue;
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/, 'corrected input must generate again');
      assert.match(tool.get('json').textContent, /fixture-token\.one-time/);
      assert.match(tool.get('state').textContent, /QR ready/);
    });
  }
}
