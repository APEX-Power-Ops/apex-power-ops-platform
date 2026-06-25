/**
 * Browser smoke: /estimator page client-side compile (proves P1 node:crypto fix)
 *
 * Safety contract:
 *   - The page hard-pins project_number = DEMO-NATIVE-001.
 *   - This test proves only the CLIENT COMPILE step (buildDemoEnvelope →
 *     estimator-core compile → content-hash via @noble/hashes).
 *   - The subsequent network submit to /api/v1/ops/intake/native is INTERCEPTED
 *     and stubbed to return a network-failure-style response so NO live ops_dev
 *     write can occur. The stub returns a non-ok HTTP response to trigger the
 *     catch branch — the test filters this from P1-failure criteria.
 *   - P1 failure = any pageerror OR any console error mentioning crypto /
 *     createHash / is not a function / module-not-found BEFORE or DURING the
 *     compile step.
 *   - A "Failed to fetch" or stubbed-network error in the catch branch is
 *     explicitly allowed and must NOT fail the test.
 *
 * Commit: test(operations-web): /estimator browser compile smoke (proves P1 node:crypto fix in-browser; no live submit)
 */

import { expect, test } from '@playwright/test'

/** Crypto / module-resolution error patterns that would indicate the P1 regression is present. */
const P1_ERROR_PATTERNS = [
  /node:crypto/i,
  /createHash/i,
  /is not a function/i,
  /Cannot find module/i,
  /Module not found/i,
  /Failed to resolve/i,
  /crypto\.createHash/i,
]

/** Network / fetch errors that are acceptable when the backend is absent. */
const ALLOWED_NETWORK_PATTERNS = [
  /Failed to fetch/i,
  /ECONNREFUSED/i,
  /NetworkError/i,
  /fetch failed/i,
  /net::ERR_/i,
  /Request failed with status/i,
  // The EstimatorError the page surfaces when fetch fails
  /TypeError.*fetch/i,
]

function isP1Error(msg: string): boolean {
  return P1_ERROR_PATTERNS.some((re) => re.test(msg))
}

function isAllowedNetworkError(msg: string): boolean {
  return ALLOWED_NETWORK_PATTERNS.some((re) => re.test(msg))
}

test('/estimator: buildDemoEnvelope compiles client-side without node:crypto crash (P1 fix)', async ({
  page,
}) => {
  const pageErrors: string[] = []
  const p1ConsoleErrors: string[] = []

  // Collect page-level JS errors (unhandled exceptions)
  page.on('pageerror', (err) => {
    pageErrors.push(err.message)
  })

  // Collect console errors, separating P1 crypto errors from allowed network noise
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text()
      if (isP1Error(text) && !isAllowedNetworkError(text)) {
        p1ConsoleErrors.push(text)
      }
    }
  })

  // --- SAFETY STUB: intercept the native intake POST so no live write reaches ops_dev ---
  // We stub before navigation so the interceptor is in place before any JS executes.
  await page.route('**/api/v1/ops/intake/**', async (route) => {
    // Return a 503 — the page's catch branch will surface "Request failed with status 503"
    // which is an allowed network error. The client compile step (buildDemoEnvelope) has
    // already run successfully at this point if we reach the fetch at all.
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Backend stubbed for browser smoke test — no live write' }),
    })
  })

  // Navigate to /estimator and assert the page loads
  const response = await page.goto('/estimator', { waitUntil: 'networkidle' })
  expect(response?.ok(), 'Page /estimator must return 200').toBeTruthy()

  // Assert the project banner renders (confirms page hydration)
  await expect(page.getByText('DEMO-NATIVE-001')).toBeVisible({ timeout: 10_000 })
  await expect(page.getByRole('heading', { name: /Estimator.*Native Renderer/i })).toBeVisible()

  // --- Step 1: Select an apparatus ref in the "Add line" select ---
  const apparatusSelect = page.getByLabel('Apparatus ref')
  await expect(apparatusSelect).toBeVisible({ timeout: 5_000 })

  // Pick the first available option (already selected by default), confirm it has options
  const optionCount = await apparatusSelect.locator('option').count()
  expect(optionCount, 'Apparatus ref select must have at least one catalog option').toBeGreaterThan(0)

  // Select the first option explicitly
  const firstRef = await apparatusSelect.locator('option').first().getAttribute('value')
  if (firstRef) {
    await apparatusSelect.selectOption(firstRef)
  }

  // --- Step 2: Set qty ---
  const qtyInput = page.getByLabel('Qty')
  await qtyInput.fill('2')

  // --- Step 3: Fill description, designation, notes ---
  await page.getByLabel('Description').fill('Smoke test circuit breaker')
  await page.getByLabel('Designation').fill('CB-SMOKE-001')
  await page.getByLabel('Notes').fill('Browser smoke test — P1 fix verification')

  // --- Step 4: Add the line ---
  await page.getByRole('button', { name: 'Add' }).click()

  // Wait for line to appear in the table (confirms React state updated)
  await expect(page.getByText('CB-SMOKE-001')).toBeVisible({ timeout: 5_000 })

  // --- Step 5: Click "Compile & Submit" ---
  // This triggers buildDemoEnvelope CLIENT-SIDE (the P1 crash point).
  // The subsequent fetch will hit our 503 stub and the page will show an error message.
  const compileBtn = page.getByRole('button', { name: /Compile & Submit/i })
  await expect(compileBtn).toBeEnabled({ timeout: 3_000 })
  await compileBtn.click()

  // Wait for the submit to complete (either success UI or error UI, never a crash)
  // The page renders an "Error" section or a success section after the async completes.
  // With our 503 stub, we expect the "Error" section to appear.
  await page.waitForFunction(
    () => {
      const body = document.body.innerText
      // Either an error section or a success section must appear
      return body.includes('Error') || body.includes('Run approved') || body.includes('Compilation findings')
    },
    { timeout: 15_000 },
  )

  // --- ASSERTIONS ---

  // P1 check: no page-level unhandled exceptions
  const p1PageErrors = pageErrors.filter(
    (msg) => isP1Error(msg) && !isAllowedNetworkError(msg),
  )
  expect(
    p1PageErrors,
    `P1 REGRESSION: unhandled page errors mentioning crypto/module resolution: ${JSON.stringify(p1PageErrors)}`,
  ).toHaveLength(0)

  // P1 check: no console errors mentioning crypto / module resolution
  expect(
    p1ConsoleErrors,
    `P1 REGRESSION: console errors mentioning crypto/module resolution: ${JSON.stringify(p1ConsoleErrors)}`,
  ).toHaveLength(0)

  // The compile step completed — the page reached the fetch (and hit our 503 stub).
  // We expect the error UI to show "Error" (from the 503 stub), NOT a module crash.
  // Verify the page does NOT show the node:crypto error text anywhere in the DOM.
  const bodyText = await page.locator('body').innerText()
  expect(bodyText, 'Page body must not contain "node:crypto"').not.toContain('node:crypto')
  expect(bodyText, 'Page body must not contain "createHash"').not.toContain('createHash')
  expect(bodyText, 'Page body must not mention "is not a function" (module crash indicator)').not.toContain(
    'is not a function',
  )

  // Confirm the page reached post-compile UI (either the error msg from the 503 or findings)
  // The key proof: if we're here without a pageerror, buildDemoEnvelope ran successfully.
  const reachedPostCompile =
    bodyText.includes('Error') ||
    bodyText.includes('Compilation findings') ||
    bodyText.includes('Run approved') ||
    bodyText.includes('Backend stubbed')
  expect(
    reachedPostCompile,
    'Page must show post-compile UI (error from stub or success) — proves compile ran without crash',
  ).toBeTruthy()
})
