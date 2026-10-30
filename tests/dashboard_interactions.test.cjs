/* Interaction checks without a browser; these do not establish rendered appearance. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../dashboard/static/js/dashboard.js'), 'utf8');

async function setup({width = 1440, plotly = true} = {}) {
  const events = {}, charts = [], navigations = [];
  const council = {
    options: [{value: 'W1', text: 'Ceredigion'}, {value: 'W2', text: 'Cardiff'}],
    disabled: false,
    replaceChildren(...options) { this.options = options; },
  };
  const region = {addEventListener(name, fn) { events.region = fn; },
    form: {requestSubmit() { events.submitted = true; }}};
  const search = {value: '', addEventListener(name, fn) { events.search = fn; },
    setCustomValidity(message) { this.message = message; }};
  const target = {on(name, fn) { events[name] = fn; }, classList: {add() {}}};
  const specs = [{title: 'Real chart', data: [{x: [1], y: [2], type: 'scatter'}], layout: {xaxis: {title: {text: 'Expected'}}}}];
  const elements = {'chart-data': {textContent: JSON.stringify(specs)}, 'chart-0': target,
    'region-filter': region, 'council-filter': council, 'council-search': search};
  const context = vm.createContext({document: {getElementById: id => elements[id]},
    window: {innerWidth: width, Plotly: plotly},
    Plotly: {async newPlot(element, data, layout, config) { charts.push({element, data, layout, config}); }},
    location: {pathname: '/councils', href: 'http://localhost:5000/councils?region=Wales', assign(url) { navigations.push(String(url)); }},
    URL, Option: function(text, value) { this.text = text; this.value = value; },
    console: {error(message) { events.error = String(message); }},
  });
  vm.runInContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return {events, charts, navigations, council, search, target};
}

test('charts receive data, responsive layout and local interaction settings', async () => {
  for (const width of [1440, 1280, 768, 390]) {
    const {charts} = await setup({width});
    assert.equal(charts.length, 1);
    assert.equal(charts[0].data[0].y[0], 2);
    assert.equal(charts[0].layout.xaxis.title.text, 'Expected');
    assert.equal(charts[0].config.responsive, true);
    assert.equal(charts[0].config.showSendToCloud, false);
  }
});

test('region changes omit previous council before submitting', async () => {
  const {events, council} = await setup();
  events.region();
  assert.equal(council.disabled, true);
  assert.equal(events.submitted, true);
});

test('council search limits options and handles no matches', async () => {
  const {events, search, council} = await setup();
  search.value = 'CERED';
  events.search();
  assert.equal(council.options.length, 1);
  assert.equal(council.options[0].value, 'W1');
  search.value = 'No such council';
  events.search();
  assert.equal(council.disabled, true);
  assert.ok(search.message);
  search.value = '';
  events.search();
  assert.equal(council.options.length, 2);
  assert.equal(council.disabled, false);
  assert.equal(search.message, '');
});

test('scatter click preserves region and selects the actual council code', async () => {
  const {events, navigations} = await setup();
  events.plotly_click({points: [{customdata: 'W1'}]});
  const url = new URL(navigations[0]);
  assert.equal(url.searchParams.get('council'), 'W1');
  assert.equal(url.searchParams.get('region'), 'Wales');
  events.plotly_click({points: [{}]});
  assert.equal(navigations.length, 1);
});

test('missing chart asset gives an honest visible error', async () => {
  const {target, events, charts} = await setup({plotly: false});
  assert.equal(charts.length, 0);
  assert.match(target.textContent, /could not load/);
  assert.match(events.error, /unavailable/);
});
