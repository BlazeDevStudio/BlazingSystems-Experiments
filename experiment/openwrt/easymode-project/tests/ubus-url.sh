#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
node - "$ROOT/installers/offline-html/EasyMode-Installer.html" <<'JS'
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = html.match(/function ubusEndpoint\(raw\)\{.*?\}/);
if (!m) throw new Error('ubusEndpoint not found');
const ubusEndpoint = new Function(m[0] + '; return ubusEndpoint;')();
const cases = [
  ['http://192.168.1.1', 'http://192.168.1.1/ubus'],
  ['http://192.168.1.1/', 'http://192.168.1.1/ubus'],
  ['http://192.168.1.1/ubus', 'http://192.168.1.1/ubus'],
  ['http://192.168.1.1/ubus/', 'http://192.168.1.1/ubus'],
  ['  http://192.168.1.1  ', 'http://192.168.1.1/ubus']
];
for (const [input, expected] of cases) {
  const got = ubusEndpoint(input);
  if (got !== expected) throw new Error(JSON.stringify(input) + ' -> ' + got);
}
let blank = false;
try { ubusEndpoint('   '); } catch (e) { blank = e.message === 'Router URL is empty'; }
if (!blank) throw new Error('blank URL was accepted');
console.log('ubus url passed');
JS
