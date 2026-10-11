const { test, expect } = require('@playwright/test');

test('Upload Prescription Test', async ({ page }) => {
  // Step 1: Open the upload page
  await page.goto('http://localhost:5173/upload');
  await page.waitForTimeout(2000);
  
  // Step 2: Take screenshot of upload page
  await page.screenshot({ path: 'screenshots/1-upload-page.png' });
  
  // Step 3: Upload the image
  await page.setInputFiles('input[type="file"]', 'prescription.jpg');
  await page.waitForTimeout(2000);
  
  // Step 4: Take screenshot after file selected
  await page.screenshot({ path: 'screenshots/2-file-selected.png' });
  
  // Step 5: Click any button that triggers upload
  // Try multiple selectors
  try {
    await page.click('button:has-text("Upload")', { timeout: 5000 });
  } catch (e) {
    try {
      await page.click('button:has-text("Process")', { timeout: 5000 });
    } catch (e2) {
      try {
        await page.click('button:has-text("Submit")', { timeout: 5000 });
      } catch (e3) {
        // If no button, just wait for auto-processing
        console.log('No button found — waiting for auto-process');
      }
    }
  }
  
  // Step 6: Wait for results
  await page.waitForTimeout(15000);
  
  // Step 7: Take screenshot of results
  await page.screenshot({ path: 'screenshots/3-results.png', fullPage: true });
  
  // Step 8: Check if results appeared
  const pageContent = await page.content();
  if (pageContent.includes('Bacin')) {
    console.log('✓ Success: Bacin found in results');
  } else if (pageContent.includes('Results')) {
    console.log('✓ Results section found');
  } else {
    console.log('✗ No results found');
  }
  
  console.log('Test completed. Check screenshots/ folder.');
});