# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: test.spec.js >> Upload Prescription Test
- Location: test.spec.js:3:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('button:has-text("Upload")')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - navigation [ref=e3]:
    - link "MediScan" [ref=e4] [cursor=pointer]:
      - /url: /
    - generic [ref=e5]:
      - link "Search" [ref=e6] [cursor=pointer]:
        - /url: /search
      - link "Upload" [ref=e7] [cursor=pointer]:
        - /url: /upload
  - main [ref=e8]:
    - generic [ref=e9]:
      - heading "Upload Prescription" [level=1] [ref=e10]
      - paragraph [ref=e11]: Upload a handwritten prescription image. Our OCR model will extract drug names and suggest alternatives.
      - img "Preview" [ref=e13] [cursor=pointer]
      - generic [ref=e14]:
        - generic [ref=e15]: prescription.jpg (171.1 KB)
        - button "Remove" [ref=e16] [cursor=pointer]
      - button "Process Prescription" [ref=e18] [cursor=pointer]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test('Upload Prescription Test', async ({ page }) => {
  4  |   // Step 1: Open the upload page
  5  |   await page.goto('http://localhost:5173/upload');
  6  |   
  7  |   // Step 2: Take screenshot of upload page
  8  |   await page.screenshot({ path: 'screenshots/1-upload-page.png' });
  9  |   
  10 |   // Step 3: Upload a prescription image
  11 |   // (Replace 'prescription.jpg' with the actual path to your test image)
  12 |   await page.setInputFiles('input[type="file"]', 'prescription.jpg');
  13 |   
  14 |   // Step 4: Click the Upload/Process button
> 15 |   await page.click('button:has-text("Upload")');
     |              ^ Error: page.click: Test timeout of 30000ms exceeded.
  16 |   
  17 |   // Step 5: Wait for results to load
  18 |   await page.waitForSelector('.results', { timeout: 30000 });
  19 |   
  20 |   // Step 6: Take screenshot of results
  21 |   await page.screenshot({ path: 'screenshots/2-results.png', fullPage: true });
  22 |   
  23 |   // Step 7: Verify drug name is extracted
  24 |   const drugName = await page.locator('.drug-name').first().textContent();
  25 |   console.log('Detected drug:', drugName);
  26 |   expect(drugName).toContain('Bacin');
  27 |   
  28 |   // Step 8: Verify alternatives are shown
  29 |   const alternatives = await page.locator('.alternatives').first().textContent();
  30 |   console.log('Alternatives:', alternatives);
  31 |   
  32 |   // Step 9: Verify confidence score
  33 |   const confidence = await page.locator('.confidence').first().textContent();
  34 |   console.log('Confidence:', confidence);
  35 | });
```