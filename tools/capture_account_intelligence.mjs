import { chromium } from '/Users/sydneychin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';

const out = new URL('../tmp/pdfs/account-intelligence/screens/', import.meta.url);
await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1.5 });
await page.addInitScript(() => localStorage.setItem('bobbee_theme', 'light'));
await page.goto('http://127.0.0.1:5488/', { waitUntil: 'networkidle' });

if (await page.locator('#loginGate').isVisible()) {
  await page.locator('#loginEmail').fill('tim.zhou@ibm.com');
  await page.locator('#loginPw').fill('demo');
  await page.locator('#loginBtn').click();
  await page.waitForSelector('#app', { state: 'visible' });
}

await page.evaluate(async () => {
  let data = await (await fetch('/api/accounts/list')).json();
  if (!data.has_accounts) {
    await fetch('/api/get_my_accounts/run', { method: 'POST' });
    for (;;) {
      const s = await (await fetch('/api/status')).json();
      if (!s._actions.get_my_accounts.active) break;
      await new Promise(r => setTimeout(r, 100));
    }
    data = await (await fetch('/api/accounts/list')).json();
  }
  if (!data.strategized) {
    await fetch('/api/strategize/run', { method: 'POST' });
    for (;;) {
      const s = await (await fetch('/api/status')).json();
      if (!s._actions.strategize.active) break;
      await new Promise(r => setTimeout(r, 100));
    }
  }
});
await page.reload({ waitUntil: 'networkidle' });
await page.waitForSelector('#dashboardBody', { state: 'visible' });
await page.waitForTimeout(800);
await page.screenshot({ path: new URL('01-dashboard.png', out).pathname, fullPage: false });

await page.locator('[data-page="accounts"]').click();
await page.waitForSelector('.acct-row:not(.acct-head)');
await page.waitForTimeout(500);
await page.screenshot({ path: new URL('02-account-book.png', out).pathname, fullPage: false });

const selected = await page.evaluate(async () => {
  const data = await (await fetch('/api/accounts/list')).json();
  const best = data.accounts.find(a => a.bucket === 'cadence' && a.tier === 1)
    || data.accounts.find(a => a.bucket === 'cadence')
    || data.accounts[0];
  return best.account;
});
await page.evaluate(name => window.openAcctModal(name), selected);
await page.waitForSelector('#acctModal.show');
await page.waitForTimeout(350);
await page.screenshot({ path: new URL('03-account-detail.png', out).pathname, fullPage: false });

await page.evaluate(() => window.closeAcctModal());
await page.locator('#profileBtn').click();
await page.waitForSelector('#page-profile.active');
await page.evaluate(() => { window.switchProfileTab('settings'); window.showSetting('intel'); });
await page.waitForTimeout(300);
await page.screenshot({ path: new URL('04-methodology.png', out).pathname, fullPage: false });

await page.evaluate(() => window.showPage('plan'));
await page.waitForSelector('#page-plan.active');
await page.waitForTimeout(500);
await page.screenshot({ path: new URL('05-schedule.png', out).pathname, fullPage: false });

await page.evaluate(() => window.showPage('cadences'));
await page.waitForSelector('#page-cadences.active');
await page.waitForTimeout(500);
await page.screenshot({ path: new URL('06-cadences.png', out).pathname, fullPage: false });

await page.evaluate(() => window.showPage('email'));
await page.waitForSelector('#page-email.active');
await page.waitForTimeout(650);
await page.screenshot({ path: new URL('07-email.png', out).pathname, fullPage: false });

await page.evaluate(() => window.showPage('call'));
await page.waitForSelector('#page-call.active');
await page.waitForTimeout(650);
await page.screenshot({ path: new URL('08-call.png', out).pathname, fullPage: false });

console.log(JSON.stringify({ selected, output: out.pathname }, null, 2));
await browser.close();
