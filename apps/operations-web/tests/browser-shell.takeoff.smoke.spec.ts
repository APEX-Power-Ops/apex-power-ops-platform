import { expect, test } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

// Paths computed with __dirname (CJS context - no import.meta.url)
const TESTS_DIR = __dirname
const OPS_WEB_DIR = path.resolve(TESTS_DIR, '..')
const REPO_ROOT = path.resolve(OPS_WEB_DIR, '..', '..')

const E01_11_PATH = path.join(
  REPO_ROOT,
  'packages',
  'estimator-takeoff',
  'test',
  'fixtures',
  'stack-phx02a-e01-11.artifact.json'
)

const CLEAN_DEMO_PATH = path.join(TESTS_DIR, 'fixtures', 'takeoff-clean-demo.artifact.json')
const REASSERT_DEMO_PATH = path.join(TESTS_DIR, 'fixtures', 'takeoff-reassert-demo.artifact.json')

// ---------------------------------------------------------------------------
// PROOF 1 - E01-11 loads and groups Voltage Questions worklist
// ---------------------------------------------------------------------------
test('Takeoff Gate 1: E01-11 loads with grouped Voltage Questions worklist', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (err) => pageErrors.push(err.message))

  await page.goto('/takeoff', { waitUntil: 'networkidle' })

  // h1 visible
  await expect(page.locator('h1')).toHaveText('Takeoff Gate 1')

  // Load E01-11 artifact
  await page.setInputFiles('input[type="file"]', E01_11_PATH)

  // Both panels render
  await expect(page.getByRole('heading', { name: 'Voltage Questions' })).toBeVisible({ timeout: 10_000 })
  await expect(page.getByRole('heading', { name: 'Other Open Items' })).toBeVisible()

  // Status banner shows partial
  const status = page.getByRole('status')
  await expect(status).toContainText('partial preview')

  // At least one Voltage-for-tag input rendered (grouped worklist)
  const voltageInputs = page.locator('input[type="number"][aria-label^="Voltage for tag "]')
  await expect(voltageInputs.first()).toBeVisible()
  const count = await voltageInputs.count()
  expect(count).toBeGreaterThan(0)

  expect(pageErrors).toHaveLength(0)
})

// ---------------------------------------------------------------------------
// PROOF 2 - Re-applying an already-asserted tag does not produce a
//           duplicate-tag error (merge dedup holds)
// ---------------------------------------------------------------------------
test('re-applying an already-asserted tag does not produce a duplicate-tag error (merge dedup holds)', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (err) => pageErrors.push(err.message))

  await page.goto('/takeoff', { waitUntil: 'networkidle' })

  // Load the 2-tag reassert fixture (FB-1, FB-2 - both LSI, both missing voltage)
  await page.setInputFiles('input[type="file"]', REASSERT_DEMO_PATH)

  await expect(page.getByRole('heading', { name: 'Voltage Questions' })).toBeVisible({ timeout: 10_000 })

  // Verify both tags surface as worklist questions
  const fb1Input = page.locator('input[aria-label="Voltage for tag FB-1"]')
  const fb2Input = page.locator('input[aria-label="Voltage for tag FB-2"]')
  await expect(fb1Input).toBeVisible()
  await expect(fb2Input).toBeVisible()

  // Fill project context (required before Apply)
  await page.fill('input[aria-label="Project number"]', 'TEST-2026-DEDUP')
  await page.fill('input[aria-label="Operator initials"]', 'JLS')

  // First Apply: enter voltage for FB-1 only
  await fb1Input.fill('480')
  await page.getByRole('button', { name: 'Apply' }).click()

  // FB-1 resolved and left the worklist; FB-2 still present
  await expect(fb2Input).toBeVisible({ timeout: 5_000 })
  // FB-1 input should no longer be in the worklist
  await expect(fb1Input).not.toBeVisible()

  // Second Apply: enter voltage for FB-2; FB-1 is already in artifact.voltageAssertions
  // and will be re-submitted through buildAssertions+mergeAssertionsByTag alongside FB-2
  await fb2Input.fill('480')
  await page.getByRole('button', { name: 'Apply' }).click()

  // (a) No duplicate-tag error text anywhere on page
  await expect(page.locator('body')).not.toContainText('voltage_assertion_duplicate_tag')

  // (b) No pageerror thrown
  expect(pageErrors).toHaveLength(0)

  // (c) Page is still functional - status banner still renders
  const status = page.getByRole('status')
  await expect(status).toBeVisible()

  // (d) Capture export and verify combined.artifact.voltageAssertions has <=1 per tag
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'partial preview - NOT a complete bid' }).click(),
  ])
  const dlPath = await download.path()
  expect(dlPath).toBeTruthy()
  {
    const parsed = JSON.parse(fs.readFileSync(dlPath!, 'utf-8'))
    const assertions: Array<{ voltageV: number; tags: string[] }> =
      parsed.artifact?.voltageAssertions ?? []
    // Count occurrences of each tag - must be <=1 per tag
    const tagCounts = new Map<string, number>()
    for (const a of assertions) {
      for (const tag of a.tags) {
        tagCounts.set(tag, (tagCounts.get(tag) ?? 0) + 1)
      }
    }
    for (const [tag, count] of tagCounts.entries()) {
      expect(count, `tag ${tag} appears ${count} times in voltageAssertions`).toBeLessThanOrEqual(1)
    }
  }
})

// ---------------------------------------------------------------------------
// PROOF 3 - Export matches status
// ---------------------------------------------------------------------------
test('Takeoff Gate 1: partial export omits envelope; clean export includes priced envelope', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (err) => pageErrors.push(err.message))

  // --- Sub-flow A: PARTIAL (E01-11) ---
  await page.goto('/takeoff', { waitUntil: 'networkidle' })
  await page.setInputFiles('input[type="file"]', E01_11_PATH)

  await expect(page.getByRole('status')).toContainText('partial preview', { timeout: 10_000 })

  await page.fill('input[aria-label="Project number"]', 'E01-TEST')
  await page.fill('input[aria-label="Operator initials"]', 'JLS')

  // Clean Export must be disabled (not clean status)
  const cleanExportBtn = page.getByRole('button', { name: 'Clean Export' })
  await expect(cleanExportBtn).toBeDisabled()

  // Partial export must be enabled
  const partialBtn = page.getByRole('button', { name: 'partial preview - NOT a complete bid' })
  await expect(partialBtn).toBeEnabled()

  // Capture partial download
  const [partialDl] = await Promise.all([
    page.waitForEvent('download'),
    partialBtn.click(),
  ])
  const partialPath = await partialDl.path()
  expect(partialPath).toBeTruthy()
  const partialParsed = JSON.parse(fs.readFileSync(partialPath!, 'utf-8'))
  // No envelope key on partial
  expect(partialParsed.envelope).toBeUndefined()
  // Status is partial_preview
  expect(partialParsed.manifest.status).toBe('partial_preview')

  // --- Sub-flow B: CLEAN (clean-demo fixture) ---
  await page.goto('/takeoff', { waitUntil: 'networkidle' })
  await page.setInputFiles('input[type="file"]', CLEAN_DEMO_PATH)

  await expect(page.getByRole('status')).toHaveText('clean', { timeout: 10_000 })

  await page.fill('input[aria-label="Project number"]', 'CLEAN-TEST')
  await page.fill('input[aria-label="Operator initials"]', 'JLS')

  // Clean Export must be enabled
  await expect(cleanExportBtn).toBeEnabled()

  // Capture clean download
  const [cleanDl] = await Promise.all([
    page.waitForEvent('download'),
    cleanExportBtn.click(),
  ])
  const cleanPath = await cleanDl.path()
  expect(cleanPath).toBeTruthy()
  const cleanParsed = JSON.parse(fs.readFileSync(cleanPath!, 'utf-8'))
  // Must have envelope with bid_cents > 0
  expect(typeof cleanParsed.envelope?.totals?.bid_cents).toBe('number')
  expect(cleanParsed.envelope.totals.bid_cents).toBeGreaterThan(0)

  expect(pageErrors).toHaveLength(0)
})
