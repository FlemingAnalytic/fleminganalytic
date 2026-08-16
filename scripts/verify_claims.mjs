// Verify what the marketing copy claims, the way it should have been done
// the first time.
//
// The previous check curled each URL for HTTP 200. The site is a single-page
// app: it answers 200 on every path, including paths with no route behind
// them, serving a 790-byte shell that renders a navbar over nothing. That
// check could not fail, so it proved nothing.
//
// This one loads each page in a real browser and asserts that something is
// actually on the screen, then checks the API behind it where there is one.
import { chromium } from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';

const SITE = 'https://fleminganalytic.com';
const API = 'https://api.fleminganalytic.com';

// The eleven claimed as applications: something you operate, not something
// you read. `api` is the endpoint that must answer for the page to be usable.
const APPS = [
    { name: 'Mars Exploration',   url: '/mars/',            api: `${API}/analyst/saved-datasets` && null, apiUrl: 'https://fleminganalytic.com/mars/api/health' },
    { name: 'Smart Analyst',      url: '/analyst',          apiUrl: `${API}/analyst/saved-datasets` },
    { name: 'AI Terminal',        url: '/chat',             apiUrl: null },
    { name: 'Restaurant Platform',url: '/restaurant',       apiUrl: `${API}/food/restaurants` },
    { name: 'Astrology Charts',   url: '/astro',            apiUrl: null },
    { name: 'Chess Game',         url: '/chess/',           apiUrl: `${API}/chess/games/count` },
    { name: 'TreeView Accounting',url: '/tvaa/',            apiUrl: null },
    { name: 'Nuclear AI Readiness', url: '/nuclear/',       apiUrl: null },
    { name: 'Energy Forecast',    url: '/energy/',          apiUrl: null },
    { name: 'Database Designer',  url: '/examples/dbdesign', apiUrl: null },
    { name: 'Church CMS',         url: '/church-cms/',      apiUrl: null },
];

// Claimed as openable but not as applications.
const REPORTS = ['/whitepaper/', '/13f/', '/hmda/', '/nport/', '/calls/', '/cms/',
                 '/complaints/', '/datacenters/', '/cars/'];
const DASHBOARDS = ['/news', '/examples/sp500', '/examples/weather', '/fred/'];

const EXTERNAL = ['https://dentaledr.net', 'https://for8thgraders.top', 'https://stubme.net'];

const browser = await chromium.launch({
    executablePath: '/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome',
    args: ['--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

/** Does the page put anything on the screen? The SPA shell does not. */
async function renders(url) {
    try {
        const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(1200);
        const m = await page.evaluate(() => ({
            text: document.body.innerText.trim().length,
            nodes: document.body.querySelectorAll('*').length,
            title: document.title,
        }));
        // The empty shell renders the navbar only: a little text, few nodes.
        const ok = m.text > 400 && m.nodes > 60;
        return { ok, status: resp?.status(), ...m };
    } catch (e) {
        return { ok: false, status: 0, text: 0, nodes: 0, title: String(e).slice(0, 40) };
    }
}

let fails = 0;
console.log('\nAPPLICATIONS — must render real content, and their API must answer\n');
for (const app of APPS) {
    const r = await renders(SITE + app.url);
    let apiNote = '';
    if (app.apiUrl) {
        try {
            const res = await fetch(app.apiUrl, { signal: AbortSignal.timeout(15000) });
            apiNote = ` · api ${res.status}`;
            if (res.status >= 500) { r.ok = false; apiNote += ' FAIL'; }
        } catch { apiNote = ' · api unreachable'; r.ok = false; }
    }
    if (!r.ok) fails++;
    console.log(`  ${r.ok ? 'OK  ' : 'FAIL'} ${app.name.padEnd(22)} ${String(r.text).padStart(5)} chars, ${String(r.nodes).padStart(4)} nodes${apiNote}`);
}

console.log('\nREPORTS — must render\n');
let reportsOk = 0;
for (const u of REPORTS) {
    const r = await renders(SITE + u);
    if (r.ok) reportsOk++; else fails++;
    console.log(`  ${r.ok ? 'OK  ' : 'FAIL'} ${u.padEnd(18)} ${String(r.text).padStart(6)} chars`);
}

console.log('\nDASHBOARDS — must render\n');
let dashOk = 0;
for (const u of DASHBOARDS) {
    const r = await renders(SITE + u);
    if (r.ok) dashOk++; else fails++;
    console.log(`  ${r.ok ? 'OK  ' : 'FAIL'} ${u.padEnd(18)} ${String(r.text).padStart(6)} chars`);
}

console.log('\nEXTERNAL — must render AND present a valid certificate\n');
let extOk = 0;
for (const u of EXTERNAL) {
    const r = await renders(u);
    if (r.ok) extOk++; else fails++;
    console.log(`  ${r.ok ? 'OK  ' : 'FAIL'} ${u.padEnd(34)} ${String(r.text).padStart(5)} chars · ${r.title.slice(0, 30)}`);
}

console.log(`\n  counted: ${APPS.length - APPS.filter((_, i) => false).length} applications claimed, ` +
            `${reportsOk} reports, ${dashOk} dashboards, ${extOk} external`);
console.log(`  ${fails === 0 ? 'EVERY CLAIM HOLDS' : `${fails} CLAIM(S) DO NOT HOLD — do not publish`}\n`);
await browser.close();
process.exit(fails ? 1 : 0);
