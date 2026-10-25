// Run the real offline template scripts and bundled QR renderer in a Node VM.
// Only the three DOM output properties and form inputs need a browser stub.
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const {URL} = require('node:url');

const root = path.join(__dirname, '..');
const qrSource = fs.readFileSync(path.join(root, 'ui/vendor/qrcode/qrcode.js'), 'utf8');
const decoderDirectory = path.join(__dirname, 'vendor/jsqr-1.4.0');
const decoderProvenance = require(path.join(decoderDirectory, 'PROVENANCE.json'));
for (const [filename, expected] of Object.entries(decoderProvenance.files)) {
  const bytes = fs.readFileSync(path.join(decoderDirectory, filename));
  assert.equal(bytes.length, expected.bytes, `test decoder ${filename} byte length changed`);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), expected.sha256,
    `test decoder ${filename} differs from pinned jsqr 1.4.0`);
}
const jsQR = require(path.join(decoderDirectory, 'jsQR.js'));
const fixtureApk = Buffer.from('Synthetic offline QR checksum fixture only.\n');
const fixtureApkUrl = 'https://example.invalid/rental-fixture.apk?source=qr-test';
const fixtureChecksum = createHash('sha256').update(fixtureApk).digest('base64url');
const provisioningFilename = 'BlazeRental-QR-Setup.template.html';
const templateSources = new Map([
  'BlazeRental-Binding-QR.template.html', provisioningFilename
].map(filename => [filename, fs.readFileSync(path.join(root, 'tools', filename), 'utf8')]));

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

function loadPage(source) {
  const nodes = new Map();
  for (const match of source.matchAll(/<(?:input|select|div|pre)\b[^>]*\bid="([^"]+)"[^>]*>/g)) {
    nodes.set(match[1], element(match[0].match(/\bvalue="([^"]*)"/)?.[1] || ''));
  }
  const context = vm.createContext({document: {getElementById: id => nodes.get(id)}, URL, TextEncoder});
  for (const match of source.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(match[1].replace('__QRCODE_JS__', () => qrSource)
      .replaceAll('__APK_URL__', fixtureApkUrl)
      .replaceAll('__APK_CHECKSUM__', fixtureChecksum), context, {timeout: 3000});
  }
  // Keep the shipped encoder and its actual modules. Intercepting its constructor
  // only exposes the symbol and input text to the independent image decoder.
  const render = context.qrcode;
  let latestSymbol, latestPayload, renderCount = 0;
  context.qrcode = new Proxy(render, {apply(target, receiver, arguments_) {
    const symbol = Reflect.apply(target, receiver, arguments_);
    const addData = symbol.addData;
    symbol.addData = (payload, mode) => {
      latestPayload = payload;
      return addData.call(symbol, payload, mode);
    };
    latestSymbol = symbol;
    renderCount++;
    return symbol;
  }});
  nodes.get('token').value = 'fixture-token.one-time';
  return {
    generate: () => context.generateQr(),
    get: id => nodes.get(id),
    symbol: () => latestSymbol,
    payload: () => latestPayload,
    renderCount: () => renderCount
  };
}

function loadTemplate(filename) {
  return loadPage(templateSources.get(filename));
}

const generatedSources = new Map();
function loadGeneratedPage(filename) {
  if (!generatedSources.has(filename)) {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'blaze-offline-qr-test-'));
    const apk = path.join(directory, 'fixture.apk');
    const template = path.join(directory, 'template.html');
    const output = path.join(directory, 'built.html');
    try {
      fs.writeFileSync(apk, fixtureApk);
      fs.writeFileSync(template, templateSources.get(filename));
      const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
      const provisioning = filename === provisioningFilename;
      const arguments_ = [path.join(root, 'tools', provisioning
        ? 'build-rental-qr-tool.py' : 'build-binding-qr-tool.py'),
      '--template', template, '--qrcode-js', path.join(root, 'ui/vendor/qrcode/qrcode.js'), '--out', output];
      if (provisioning) arguments_.push('--apk', apk, '--apk-url', fixtureApkUrl);
      const result = spawnSync(python, arguments_, {encoding: 'utf8', timeout: 30000});
      assert.ifError(result.error);
      assert.equal(result.status, 0, result.stderr);
      const source = fs.readFileSync(output, 'utf8');
      assert.doesNotMatch(source,
        /__QRCODE_JS__|__APK_URL__|__APK_CHECKSUM__|__BLAZE_SYSTEMS_LOGO__/,
        'actual builder left an unresolved offline-page marker');
      generatedSources.set(filename, source);
    } finally {
      for (const filename of [apk, template, output]) {
        if (fs.existsSync(filename)) fs.unlinkSync(filename);
      }
      fs.rmdirSync(directory);
    }
  }
  return loadPage(generatedSources.get(filename));
}

function setInputs(tool, inputs) {
  for (const [field, value] of Object.entries(inputs)) tool.get(field).value = value;
}

function readQr(tool) {
  assert.match(tool.get('qr').innerHTML, /<svg\b/, 'valid input must generate a real QR');
  assert.match(tool.get('state').textContent, /QR ready/);
  const symbol = tool.symbol();
  const scale = 4, quietModules = 4;
  const side = (symbol.getModuleCount() + quietModules * 2) * scale;
  const rgba = new Uint8ClampedArray(side * side * 4).fill(255);
  for (let row = 0; row < symbol.getModuleCount(); row++) {
    for (let column = 0; column < symbol.getModuleCount(); column++) {
      if (!symbol.isDark(row, column)) continue;
      for (let y = 0; y < scale; y++) {
        for (let x = 0; x < scale; x++) {
          const offset = (((row + quietModules) * scale + y) * side
            + (column + quietModules) * scale + x) * 4;
          rgba[offset] = rgba[offset + 1] = rgba[offset + 2] = 0;
        }
      }
    }
  }
  const decoded = jsQR(rgba, side, side, {inversionAttempts: 'dontInvert'});
  assert.ok(decoded, 'independent decoder could not read the actual QR module matrix');
  assert.deepEqual(Array.from(decoded.binaryData), Array.from(Buffer.from(tool.payload(), 'utf8')),
    'actual QR byte payload differs from the UTF-8 JSON shown on the page');
  assert.equal(decoded.data, tool.payload(), 'decoded QR text differs from its source JSON');
  const payload = JSON.parse(decoded.data);
  assert.deepEqual(payload, JSON.parse(tool.get('json').textContent),
    'scanned QR and displayed JSON must contain identical values');
  if ('android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE' in payload) {
    assert.equal(payload['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION'], fixtureApkUrl);
    assert.equal(payload['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM'], fixtureChecksum);
  }
  return payload;
}

const templates = [
  ['binding', 'BlazeRental-Binding-QR.template.html'],
  ['Device Owner', 'BlazeRental-QR-Setup.template.html']
];
const invalidInputs = [
  ['invalid server', 'server', 'invalid'],
  ['missing server', 'server', ''],
  ['missing server hostname', 'server', 'https://'],
  ['nonnumeric server port', 'server', 'https://example.invalid:abc'],
  ['out-of-range server port', 'server', 'https://example.invalid:65536'],
  ['missing token', 'token', ''],
  ['invalid certificate pin', 'certPin', 'not-a-sha256']
];

for (const [label, filename] of templates) {
  const cases = label === 'binding'
    ? [...invalidInputs, ['invalid token format', 'token', 'missing-separator']]
    : [...invalidInputs, ['HTTP server', 'server', 'http://example.invalid:8080']];
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
  const validServers = ['https://EXAMPLE.invalid:443', 'https://example.invalid:8443'];
  if (label === 'binding') validServers.push('http://example.invalid:80', 'http://192.168.1.1:8080');
  for (const server of validServers) {
    test(`${label}: valid server ${server} keeps its original payload text`, () => {
      const tool = loadTemplate(filename);
      tool.get('server').value = server;
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/, 'valid input must generate a real QR');
      assert.match(tool.get('state').textContent, /QR ready/);
      const payload = JSON.parse(tool.get('json').textContent);
      const binding = payload['android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE'] || payload;
      assert.equal(binding.server_url, server, 'validation must not normalize the saved server URL');
      assert.equal(binding.enrollment_token, 'fixture-token.one-time');
    });
  }
}

const wifiSsid = 'android.app.extra.PROVISIONING_WIFI_SSID';
const wifiSecurity = 'android.app.extra.PROVISIONING_WIFI_SECURITY_TYPE';
const wifiPassword = 'android.app.extra.PROVISIONING_WIFI_PASSWORD';
const pageKinds = [
  ['template', () => loadTemplate(provisioningFilename)],
  ['generated HTML', () => loadGeneratedPage(provisioningFilename)]
];
const validWifi = [
  ['one-byte SSID and eight-character WPA password', 'a', 'a'.repeat(8)],
  ['32-byte SSID and 63-character WPA password', 'a'.repeat(32), 'a'.repeat(63)],
  ['literal leading and trailing spaces', ' Cafe ', ' 123456 '],
  ['one-space SSID', ' ', '12345678'],
  ['literal outer quotes', '"Cafe"', '"123456"'],
  ['embedded quote', 'Room "A"', 'a"bcdefg'],
  ['literal backslash', 'Cafe\\Room', 'abc\\defg'],
  ['32-byte SSID including literal outer quotes', '"' + 'a'.repeat(30) + '"', '12345678'],
  ['63-character WPA password including edge spaces', 'Cafe', ' ' + 'a'.repeat(61) + ' '],
  ['eight-space WPA password', 'Cafe', ' '.repeat(8)],
  ['eight two-byte Unicode WPA characters', 'Cafe', 'é'.repeat(8)],
  ['63-byte Unicode WPA password', 'Cafe', 'é'.repeat(31) + 'a'],
  ['eight four-byte Unicode WPA characters', 'Cafe', '😀'.repeat(8)],
  ['four supplementary WPA characters meet Android UTF-16 minimum', 'Cafe', '😀'.repeat(4)],
  ['32-byte two-byte Unicode SSID', 'é'.repeat(16), '12345678'],
  ['32-byte three-byte Unicode SSID', '网'.repeat(10) + 'ab', '12345678'],
  ['32-byte four-byte Unicode SSID', '😀'.repeat(8), '12345678'],
  ['mixed Unicode SSID', 'Café 网络 😀', '12345678']
];
const invalidWifi = [
  ['WPA without SSID', {ssid: ''}, /SSID/],
  ['open network without SSID', {security: 'NONE', ssid: ''}, /SSID/],
  ['33-byte ASCII SSID', {ssid: 'a'.repeat(33)}, /SSID/],
  ['33-byte SSID including leading space', {ssid: ' ' + 'a'.repeat(32)}, /SSID/],
  ['33-byte two-byte Unicode SSID', {ssid: 'é'.repeat(16) + 'a'}, /SSID/],
  ['33-byte three-byte Unicode SSID', {ssid: '网'.repeat(11)}, /SSID/],
  ['33-byte four-byte Unicode SSID', {ssid: '😀'.repeat(8) + 'a'}, /SSID/],
  ['open network with 33-byte SSID', {security: 'NONE', ssid: 'a'.repeat(33)}, /SSID/],
  ['empty WPA password', {wifiPass: ''}, /password/i],
  ['seven-character WPA password', {wifiPass: 'a'.repeat(7)}, /password/i],
  ['64-character WPA password', {wifiPass: 'a'.repeat(64)}, /password/i],
  ['64-character WPA password including leading space', {wifiPass: ' ' + 'a'.repeat(63)}, /password/i],
  ['four WPA characters despite eight UTF-8 bytes', {wifiPass: 'é'.repeat(4)}, /password/i],
  ['seven UTF-16 WPA units despite 13 UTF-8 bytes', {wifiPass: '😀'.repeat(3) + 'a'}, /password/i],
  ['64-byte Unicode WPA password', {wifiPass: 'é'.repeat(31) + 'ab'}, /password/i],
  ['64-byte four-byte Unicode WPA password', {wifiPass: '😀'.repeat(16)}, /password/i]
];

for (const [kind, load] of pageKinds) {
  for (const [label, ssid, password] of validWifi) {
    test(`Device Owner ${kind}: QR round trip preserves ${label}`, () => {
      const tool = load();
      setInputs(tool, {security: 'WPA', ssid, wifiPass: password});
      tool.generate();
      const payload = readQr(tool);
      assert.equal(payload[wifiSsid], ssid, 'Wi-Fi SSID must retain its literal input identity');
      assert.equal(payload[wifiPassword], password, 'Wi-Fi password must retain its literal input identity');
      assert.equal(payload[wifiSecurity], 'WPA');
    });
  }

  test(`Device Owner ${kind}: open network preserves SSID and omits a filled password`, () => {
    const tool = load();
    const ssid = ' Open "Cafe"\\ ';
    setInputs(tool, {security: 'NONE', ssid, wifiPass: 'ignored-filled-password'});
    tool.generate();
    const payload = readQr(tool);
    assert.equal(payload[wifiSsid], ssid);
    assert.equal(payload[wifiSecurity], 'NONE');
    assert.equal(wifiPassword in payload, false);
  });

  test(`Device Owner ${kind}: omitting optional Wi-Fi removes every Wi-Fi field`, () => {
    const tool = load();
    setInputs(tool, {security: 'WPA', ssid: 'Cafe', wifiPass: '12345678'});
    tool.generate();
    assert.match(tool.get('qr').innerHTML, /<svg\b/);
    for (const inputs of [
      {security: '', ssid: 'unused'.repeat(12), wifiPass: 'short'},
      {security: '', ssid: '', wifiPass: ''}
    ]) {
      setInputs(tool, inputs);
      tool.generate();
      const payload = readQr(tool);
      for (const field of [wifiSsid, wifiSecurity, wifiPassword]) assert.equal(field in payload, false);
    }
  });

  for (const [label, invalid, expectedError] of invalidWifi) {
    test(`Device Owner ${kind}: ${label} clears previous QR and recovers after correction`, () => {
      const tool = load();
      const valid = {security: 'WPA', ssid: 'Cafe', wifiPass: '12345678'};
      setInputs(tool, valid);
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/);
      assert.match(tool.get('state').textContent, /QR ready/);
      const previousRenders = tool.renderCount();
      setInputs(tool, invalid);
      tool.generate();
      assert.equal(tool.get('qr').innerHTML, '', 'failed retry leaves an old scannable QR');
      assert.equal(tool.get('json').textContent, '', 'failed retry leaves reusable old JSON');
      assert.match(tool.get('state').textContent, expectedError);
      assert.doesNotMatch(tool.get('state').innerHTML, /class="ok"|QR ready/);
      assert.equal(tool.renderCount(), previousRenders, 'invalid Wi-Fi reached the QR renderer');
      setInputs(tool, valid);
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/);
      assert.match(tool.get('state').textContent, /QR ready/);
      const corrected = JSON.parse(tool.get('json').textContent);
      assert.equal(corrected[wifiSsid], valid.ssid);
      assert.equal(corrected[wifiPassword], valid.wifiPass);
    });
  }

  test(`Device Owner ${kind}: WPA password refuses every ASCII control character and clears prior output`, () => {
      const field = 'wifiPass';
      const tool = load();
      const valid = {security: 'WPA', ssid: 'Cafe', wifiPass: '12345678'};
      setInputs(tool, valid);
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/);
      const previousRenders = tool.renderCount();
      for (const code of [...Array.from({length: 32}, (_, index) => index), 127]) {
        setInputs(tool, {...valid, [field]: 'Cafe' + String.fromCharCode(code) + 'Room'});
        tool.generate();
        const label = `${field} U+${code.toString(16).padStart(4, '0')}`;
        assert.equal(tool.get('qr').innerHTML, '', `${label} left a scannable QR`);
        assert.equal(tool.get('json').textContent, '', `${label} left reusable JSON`);
        assert.notEqual(tool.get('state').textContent, '', `${label} needs a visible error`);
        assert.doesNotMatch(tool.get('state').innerHTML, /class="ok"|QR ready/, label);
        assert.equal(tool.renderCount(), previousRenders, `${label} reached the renderer`);
      }
      setInputs(tool, valid);
      tool.generate();
      assert.match(tool.get('qr').innerHTML, /<svg\b/);
      assert.match(tool.get('state').textContent, /QR ready/);
  });
}

const bindingFilename = 'BlazeRental-Binding-QR.template.html';
const bindingPages = [
  ['template', () => loadTemplate(bindingFilename)],
  ['generated HTML', () => loadGeneratedPage(bindingFilename)]
];
for (const name of ['Rental é', 'Rental 网', 'Rental 😀', 'Rental Café 网络 😀']) {
  for (const [kind, load] of bindingPages) {
    test(`binding ${kind}: independent QR decode preserves Unicode device_name ${JSON.stringify(name)}`, () => {
      const tool = load();
      setInputs(tool, {name});
      tool.generate();
      const payload = readQr(tool);
      assert.equal(payload.device_name, name);
      assert.equal(payload.enrollment_token, 'fixture-token.one-time');
      assert.equal(payload.server_url, 'https://192.168.1.1:8443');
    });
  }
}
