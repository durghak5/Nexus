const { test, expect } = require('@playwright/test');
const path = require('path');

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:5173';
const SAMPLE_IMAGE = path.join(__dirname, 'fixtures', 'sample_prescription_1.jpg');

test.describe('Medical Prescription OCR System', () => {

  test.beforeAll(async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`).catch(() => null);
    if (!response || !response.ok()) {
      throw new Error(
        `❌ Backend not running at ${BACKEND_URL}.\n` +
        `   Start it with: uvicorn app.main:app --reload`
      );
    }
  });

  test('Upload prescription and get OCR results', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);
    await expect(page.locator('h1')).toContainText('Upload Prescription');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(SAMPLE_IMAGE);

    await expect(page.locator('.preview-img')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.file-info')).toContainText('.jpg');

    const processButton = page.locator('button', { hasText: 'Process Prescription' });
    await expect(processButton).toBeEnabled();
    await processButton.click();

    await expect(page.locator('.loading-box')).toBeVisible({ timeout: 5000 });

    await expect(page.locator('.results')).toBeVisible({ timeout: 60000 });

    await expect(page.locator('.summary')).toBeVisible();
    await expect(page.locator('.summary-value').first()).not.toHaveText('0');

    const drugCards = page.locator('.drug-card');
    await expect(drugCards.first()).toBeVisible();

    await expect(page.locator('.drug-card').filter({ hasText: 'Augmentin' })).toBeVisible();

    await expect(page.locator('.alt-list li').first()).toBeVisible();
  });

  test('Rejects non-image files', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);

    const textFile = {
      name: 'fake.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('not an image'),
    };

    await page.locator('input[type="file"]').setInputFiles(textFile);

    await expect(page.locator('.error-box')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('.error-box')).toContainText('image');
  });

  test('Process another prescription after result', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);
    await page.locator('input[type="file"]').setInputFiles(SAMPLE_IMAGE);
    await page.locator('button', { hasText: 'Process Prescription' }).click();

    await expect(page.locator('.results')).toBeVisible({ timeout: 60000 });
    await page.locator('button', { hasText: 'Process another' }).click();

    await expect(page.locator('.drop-zone')).toBeVisible();
    await expect(page.locator('.results')).not.toBeVisible();
  });
});