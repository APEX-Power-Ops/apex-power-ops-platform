import { expect, test } from '@playwright/test'

test('root shell renders and blocks invalid apparatus IDs before backend fetch', async ({
  page,
}) => {
  let apparatusResourceRequests = 0

  await page.route('**/api/v1/neta/apparatus/*/resources', async (route) => {
    apparatusResourceRequests += 1
    await route.abort()
  })

  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'Operations Web now has a real frontend boundary.' }),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Validation Surface' })).toBeVisible()

  await page.getByLabel('Apparatus UUID').fill('invalid-id')
  await page.getByRole('button', { name: 'Load Resources' }).click()

  await expect(
    page.getByText('Enter a valid apparatus UUID to read the governed backend study-resource seam.'),
  ).toBeVisible()
  expect(apparatusResourceRequests).toBe(0)

  await page.getByRole('button', { name: 'Clear' }).click()
  await expect(page.getByLabel('Apparatus UUID')).toHaveValue('')
  await expect(
    page.getByText('Enter a valid apparatus UUID to read the governed backend study-resource seam.'),
  ).toBeHidden()
  await expect(
    page.getByText('Enter an apparatus UUID to exercise the new governed backend route from the browser shell.'),
  ).toBeVisible()
  expect(apparatusResourceRequests).toBe(0)
})
