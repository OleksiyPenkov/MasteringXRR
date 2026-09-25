import { expect, test } from '@playwright/test';
import { BASE } from '../src/lib/site.mjs';

test('home lists the Introduction under Front Matter', async ({ page }) => {
  await page.goto(`${BASE}/`);
  await expect(page.getByRole('heading', { name: 'Front Matter' })).toBeVisible();
  await page.getByRole('link', { name: /Introduction/ }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Introduction' })).toBeVisible();
});

test('the Introduction carries the five sections of STYLE.md §3', async ({ page }) => {
  await page.goto(`${BASE}/introduction/`);
  for (const name of ['About This Book', 'Foolish Assumptions', 'Icons Used in This Book', 'Beyond the Book', 'Where to Go from Here']) {
    await expect(page.getByRole('heading', { level: 2, name })).toBeVisible();
  }
});

test('on screen, web-only shows and print-only is hidden', async ({ page }) => {
  await page.goto(`${BASE}/sampler/`);
  await expect(page.getByText('WEB-ONLY:')).toBeVisible();
  await expect(page.getByText('PRINT-ONLY:')).toBeHidden();
});

test('printing swaps them', async ({ page }) => {
  await page.goto(`${BASE}/sampler/`);
  await page.emulateMedia({ media: 'print' });
  await expect(page.getByText('PRINT-ONLY:')).toBeVisible();
  await expect(page.getByText('WEB-ONLY:')).toBeHidden();
});

test('Going Deeper is collapsed on the web and opens on click', async ({ page }) => {
  await page.goto(`${BASE}/sampler/`);
  const box = page.locator('details.box-deeper');
  await expect(box).not.toHaveAttribute('open', '');
  await box.locator('summary').click();
  await expect(box.locator('.katex-display')).toBeVisible();
});

test('Sources is collapsed on the web, keeps its #sources id, and opens on click', async ({ page }) => {
  await page.goto(`${BASE}/ch9-how-x-ray-calc-finds-a-fit/`);
  const box = page.locator('details.sources-section');
  await expect(box).toHaveCount(1);
  await expect(box).not.toHaveAttribute('open', '');
  await expect(box.locator('summary h2#sources')).toBeVisible();
  await expect(box.locator('ul').first()).toBeHidden();
  await box.locator('summary').click();
  await expect(box.locator('ul').first()).toBeVisible();
});

test('a figure opens full size on click and closes with Escape', async ({ page }) => {
  await page.goto(`${BASE}/ch9-how-x-ray-calc-finds-a-fit/`);
  const dialog = page.locator('dialog.figzoom');
  await expect(dialog).toBeHidden();
  await page.locator('#fig-9-1 img').click();
  await expect(dialog).toBeVisible();
  await expect(dialog.locator('.figzoom-img')).toBeVisible();
  await expect(dialog.locator('.figzoom-caption')).toContainText('Figure 9-1');
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await page.locator('#fig-9-3 svg').click();
  await expect(dialog.locator('.figzoom-svg')).toBeVisible();
  await expect(dialog.locator('.figzoom-open')).toBeHidden();
});

test('the period-from-orders widget computes D and recomputes live', async ({ page }) => {
  await page.goto(`${BASE}/sampler/`);
  const widget = page.locator('.widget.period-from-orders');
  await expect(widget).toContainText('54.70');
  // client:visible: scroll it in, then wait for Astro to hydrate the island.
  await widget.scrollIntoViewIfNeeded();
  await expect(page.locator('astro-island', { has: widget })).not.toHaveAttribute('ssr', '');
  await widget.getByRole('button', { name: 'Add an order' }).click();
  await widget.getByLabel('Measured 2θ in degrees, row 7').fill('11.3365');
  // D scales with λ: at Kα1 alone the seven orders give 54.65 Å (54.70 at the file's λ).
  await widget.getByLabel(/λ/).fill('1.540598');
  await expect(widget).toContainText('54.65');
  await widget.getByRole('button', { name: 'Reset to the CoC4 example' }).click();
  await expect(widget.getByLabel('Measured 2θ in degrees, row 7')).toHaveCount(0);
  await expect(widget).toContainText('54.70');
});

test('the sensitivity-check widget loads its curves and changes one parameter', async ({ page }) => {
  // Server-rendered: the loading text, and the controls disabled until the curves arrive.
  const html = await (await page.request.get(`${BASE}/sampler/`)).text();
  const ssr = html.slice(html.indexOf('widget sensitivity-check'));
  expect(ssr).toContain('Loading the precomputed curves');
  expect(ssr).toMatch(/<fieldset[^>]*disabled/);
  await page.goto(`${BASE}/sampler/`);
  const widget = page.locator('.widget.sensitivity-check');
  await widget.scrollIntoViewIfNeeded();
  await expect(page.locator('astro-island', { has: widget })).not.toHaveAttribute('ssr', '');
  const readout = widget.locator('.readout');
  await expect(readout).toHaveText('Period D: 54.70 Å (starting model)');
  await expect(widget.locator('path.measured')).toHaveCount(1);
  await expect(widget.locator('path.base')).toHaveCount(1);
  await expect(widget.locator('path.variant')).toHaveCount(0);

  await widget.getByLabel('σ of Co').check();
  await expect(readout).toHaveText('σ of Co: 4 Å (starting model)');
  const slider = widget.getByLabel('Value');
  await slider.focus();
  await page.keyboard.press('ArrowRight');
  await expect(readout).toHaveText('σ of Co: 6 Å');
  const variant = widget.locator('path.variant');
  await expect(variant).toHaveCount(1);
  const d6 = await variant.getAttribute('d');
  await page.keyboard.press('ArrowRight');
  await expect(readout).toHaveText('σ of Co: 8 Å');
  await expect(variant).not.toHaveAttribute('d', d6!);
  // Another parameter resets the slider to the starting model.
  await widget.getByLabel('Number of periods N').check();
  await expect(readout).toHaveText('Number of periods N: 20 (starting model)');
  await expect(variant).toHaveCount(0);
});
