const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const root = __dirname;
const fragment = fs.readFileSync(path.join(root, 'native-menu-design.html'), 'utf8');
const standalone = fs.readFileSync(path.join(root, 'native-menu-design-preview.html'), 'utf8');
for (const source of [fragment, standalone]) {
  assert(!/\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(|<(?:script|link|iframe)[^>]+(?:src|href)=/.test(source));
  for (const match of source.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(match[1]);
  const png = Buffer.from(source.match(/data:image\/png;base64,([^"\s]+)/)[1], 'base64');
  assert(png.equals(fs.readFileSync(path.join(root, '../../assets/sprites/fox/idle/frame_1.png'))));
}
assert(standalone.includes("connect-src 'none'"));
assert(!/data-lucide|aria-label="Кольцо" hidden/.test(standalone));
const sections = [0, 1].map(() => {
  const submenu = {hidden: true};
  const more = {attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }};
  const status = {textContent: ''};
  return {submenu, more, status, listeners: {},
    querySelector(selector) { return selector === 'output' ? status : selector === '.nd-more' ? more : submenu; },
    addEventListener(name, handler) { this.listeners[name] = handler; }};
});
const script = [...fragment.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
vm.runInNewContext(script, {document: {getElementById: () => ({querySelectorAll: () => sections})}});
for (const section of sections) {
  const button = {classList: {contains: () => true}, setAttribute() {}};
  section.listeners.click({target: {closest: () => button}});
  assert.equal(section.submenu.hidden, false);
  section.listeners.keydown({key: 'Escape'});
  assert.equal(section.submenu.hidden, true);
  const primary = {classList: {contains: () => false}, getAttribute: () => null, textContent: 'Мяч'};
  section.listeners.click({target: {closest: () => primary}});
  assert.equal(section.status.textContent, 'Мяч');
}
console.log('PASS: offline resources, exact original PNG, script syntax, both variant actions/More/Escape');
