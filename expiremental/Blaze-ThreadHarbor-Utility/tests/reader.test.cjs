// Synthetic DOM validation of the user-invoked native reader parser.
// This does not prove compatibility with a live website or Android WebView.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const kotlin = fs.readFileSync(path.join(__dirname, '../app/src/main/java/com/blazesystems/threadharbor/ReaderScreen.kt'), 'utf8');
const script = kotlin.match(/private val readerScript = """([\s\S]*?)"""/)?.[1];
assert.ok(script, 'Kotlin must expose the exact in-app reading script');

function element(innerText, excluded = false, hidden = false) {
  return {
    innerText,
    closest(selector) { assert.ok(selector.includes('form')); return excluded ? this : null; },
    hidden,
  };
}
const secret = 'ENCRYPTION PIN 5423045981234567';
const dom = [
  element('A useful, publicly visible article heading'),
  element(secret, true),
  element('This text is hidden and should be ignored by the native reader.', false, true),
  element('This paragraph contains actual visible informational content from the document.'),
];
const result = JSON.parse(vm.runInNewContext(script, {
  document: {
    title: 'A real document in an authorized webview',
    querySelectorAll: () => dom,
  },
  location: { href: 'https://example.org/news/123' },
  window: { getComputedStyle: node => ({
    display: node.hidden ? 'none' : 'block', visibility: 'visible'
  }) },
  JSON,
}));
assert.equal(result.title, 'A real document in an authorized webview');
assert.equal(result.url, 'https://example.org/news/123');
assert.equal(result.sections.length, 2);
assert.ok(!JSON.stringify(result).includes(secret));
assert.equal(result.sections[0], dom[0].innerText);
assert.equal(result.sections[1], dom[3].innerText);
assert.ok(!script.includes('input.value'));
assert.ok(!script.includes('document.cookie'));
console.log('PASS: opted-in native reader extracts visible article blocks, excludes forms and hidden content (synthetic DOM only)');
