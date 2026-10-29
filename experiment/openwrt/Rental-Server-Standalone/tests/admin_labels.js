'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../root/www/rental/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'operator dashboard script missing');
const deviceId = '0123456789abcdef01234567';
const cases = [
  ['plain', 'Test phone'],
  ['apostrophe', "O'Brien"],
  ['double quotes and markup', 'Family "A" & <friends>'],
  ['backslash', 'Back\\slash'],
  ['trailing backslash', 'Trailing\\'],
  ['code-shaped data', "');labelProbe++; //"],
  ['Unicode', 'Cafe\u0301 \u706b \ud83d\udd25'],
  ['entity-looking data', '&quot; &#39; &amp;'],
];

function page(label) {
  const elements = new Map();
  const requests = [];
  const prompts = [];
  const context = vm.createContext({
    document: { getElementById(id) {
      if (!elements.has(id)) elements.set(id, { innerHTML: '', textContent: '', classList: { add() {}, remove() {} } });
      return elements.get(id);
    } },
    location: { origin: 'https://r281.invalid' },
    sessionStorage: { getItem() { return null; } },
    URLSearchParams,
    labelProbe: 0,
    prompt(message, current) { prompts.push({ message, current }); return 'Renamed phone'; },
    alert(message) { throw Error('Unexpected alert: ' + message); },
    async fetch(url, options) {
      assert.equal(url, '/cgi-bin/rental-admin');
      assert.equal(options.method, 'POST');
      const body = new URLSearchParams(options.body);
      requests.push(body);
      const action = body.get('action');
      assert.ok(['list', 'rename', 'recent_events'].includes(action), 'unexpected operator action');
      const result = action === 'list'
        ? { ok: true, devices: [{ device_id: deviceId, label, remaining: 3600, last_seen: 0 }] }
        : action === 'recent_events' ? { ok: true, events: [] } : { ok: true };
      return { async json() { return result; } };
    },
  });
  vm.runInContext(script, context, { filename: 'rental-dashboard.js' });
  return { context, elements, requests, prompts };
}

// HTML entities are decoded before an inline event handler is compiled. Use an
// independent standard-library HTML parser, not the renderer's escaping helper.
const decodeButtons = String.raw`
from html.parser import HTMLParser
import json, sys
class Buttons(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.buttons = []
    def handle_starttag(self, tag, attrs):
        if tag == 'button': self.current = {'attrs': dict(attrs), 'text': ''}
    def handle_data(self, data):
        if self.current is not None: self.current['text'] += data
    def handle_endtag(self, tag):
        if tag == 'button' and self.current is not None:
            self.buttons.append(self.current)
            self.current = None
result = []
for markup in json.load(sys.stdin):
    parser = Buttons()
    parser.feed(markup)
    buttons = [item['attrs'] for item in parser.buttons if item['text'] == 'Rename']
    assert len(buttons) == 1, 'expected one Rename control'
    result.append(buttons[0])
json.dump(result, sys.stdout, ensure_ascii=True)
`;

(async () => {
  const pages = cases.map(([, label]) => page(label));
  const markup = [];
  for (const current of pages) {
    await current.context.refreshDevices();
    markup.push(current.elements.get('devices').innerHTML);
  }
  const decoded = spawnSync(process.env.PYTHON || 'python3', ['-X', 'utf8', '-c', decodeButtons], {
    input: JSON.stringify(markup), encoding: 'utf8', timeout: 30000,
  });
  if (decoded.error) throw decoded.error;
  assert.equal(decoded.status, 0, decoded.stderr || 'HTML parser failed');
  const attributes = JSON.parse(decoded.stdout);
  assert.equal(attributes.length, cases.length);
  let failed = 0;
  for (let index = 0; index < cases.length; index++) {
    const [name, label] = cases[index];
    const current = pages[index];
    const attrs = attributes[index];
    current.context.button = { dataset: { label: attrs['data-label'] } };
    let callbackError;
    try {
      vm.runInContext('(function(event){' + attrs.onclick + '\n}).call(button)', current.context);
    } catch (error) { callbackError = error; }
    // The real renameDev/api implementation uses already-resolved fixture
    // fetch promises; drain them before observing the prompt and POST boundary.
    await new Promise(resolve => setImmediate(resolve));
    try {
      assert.equal(callbackError, undefined, 'rendered Rename handler must compile');
      assert.equal(current.context.labelProbe, 0, 'label data must never execute');
      assert.equal(current.prompts.length, 1, 'Rename must open exactly one dialog');
      assert.equal(current.prompts[0].current, label, 'dialog must receive the literal stored label');
      const renames = current.requests.filter(body => body.get('action') === 'rename');
      assert.equal(renames.length, 1, 'Rename must send one existing API operation');
      assert.equal(renames[0].get('device_id'), deviceId);
      assert.equal(renames[0].get('label'), 'Renamed phone');
      console.log('PASS: ' + name);
    } catch (error) {
      failed++;
      console.error('FAIL: ' + name + ': ' + error.message);
    }
  }
  console.log('Standalone Rename labels: ' + (cases.length - failed) + '/' + cases.length + ' passed');
  if (failed) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
