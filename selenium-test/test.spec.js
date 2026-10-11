const { test, expect } = require('@playwright/test');

test('Upload Prescription Test', async ({ page }) => {
  // Step 1: Open the upload page
  await page.goto('http://localhost:5173/upload');
  
  // Step 2: Take screenshot of upload page
  await page.screenshot({ path: 'screenshots/1-upload-page.png' });
  
  // Step 3: Upload a prescription image
  // (Replace 'prescription.jpg' with the actual path to your test image)
  await page.setInputFiles('input[type="file"]', 'prescription.jpg');
  
  // Step 4: Click the Upload/Process button
  await page.click('button:has-text("Upload")');
  
  // Step 5: Wait for results to load
  await page.waitForSelector('.results', { timeout: 30000 });
  
  // Step 6: Take screenshot of results
  await page.screenshot({ path: 'screenshots/2-results.png', fullPage: true });
  
  // Step 7: Verify drug name is extracted
  const drugName = await page.locator('.drug-name').first().textContent();
  console.log('Detected drug:', drugName);
  expect(drugName).toContain('Bacin');
  
  // Step 8: Verify alternatives are shown
  const alternatives = await page.locator('.alternatives').first().textContent();
  console.log('Alternatives:', alternatives);
  
  // Step 9: Verify confidence score
  const confidence = await page.locator('.confidence').first().textContent();
  console.log('Confidence:', confidence);
});