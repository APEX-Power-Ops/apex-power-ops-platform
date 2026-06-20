import { test, expect } from '@playwright/test'

const USER = '00000000-0000-0000-0000-000000000001'
const SC = 'aaaaaaaa-1111-1111-1111-111111111111'

test.describe('learning-demo capture loop', () => {
  test('marks a resource viewed and renders the captured event', async ({ page }) => {
    const captured: Array<Record<string, unknown>> = []

    await page.route('**/api/v1/learning/users**', (route) =>
      route.fulfill({ json: { users: [{ id: USER, email: 'tech1@example.com' }] } }),
    )
    await page.route('**/api/v1/learning/sections**', (route) =>
      route.fulfill({ json: { sections: ['7.2.1.1', '7.6.1.1.1'] } }),
    )
    await page.route('**/api/v1/learning/resources**', (route) =>
      route.fulfill({
        json: {
          context: { neta_section: '7.2.1.1', level: null, limit: 20 },
          resources: [{
            resource_type: 'study_content', title: 'Breaker basics', source: 'curated',
            reference: { kind: 'study_content', id: SC }, is_primary: true, is_mandatory: false,
            cert_level: 'II', score: 1100, why: 'curated resource for this apparatus type',
          }],
        },
      }),
    )
    await page.route('**/api/v1/learning/events**', async (route) => {
      const req = route.request()
      if (req.method() === 'POST') {
        const body = req.postDataJSON() as Record<string, unknown>
        captured.push(body)
        await route.fulfill({
          json: {
            event: {
              event_id: `e${captured.length}`, user_id: body.user_id, event_type: body.event_type,
              study_content_id: body.study_content_id ?? null, neta_section: body.neta_section ?? null,
              occurred_at: new Date().toISOString(), payload: body.payload ?? {}, created_at: new Date().toISOString(),
            },
          },
        })
      } else {
        await route.fulfill({
          json: {
            events: captured.map((b, i) => ({
              event_id: `e${i + 1}`, user_id: b.user_id, event_type: b.event_type,
              study_content_id: b.study_content_id ?? null, neta_section: b.neta_section ?? null,
              occurred_at: new Date().toISOString(), payload: b.payload ?? {}, created_at: new Date().toISOString(),
            })),
          },
        })
      }
    })

    await page.goto('/learning-demo')
    await page.getByRole('button', { name: 'Resolve' }).click()
    await expect(page.getByRole('heading', { name: 'Breaker basics' })).toBeVisible()

    await page.getByRole('button', { name: 'Mark viewed' }).first().click()
    await expect.poll(() => captured.length).toBeGreaterThan(0)
    expect(captured[0]).toMatchObject({
      user_id: USER, event_type: 'resource_viewed', neta_section: '7.2.1.1', study_content_id: SC,
    })
    await expect(page.getByText('resource_viewed').first()).toBeVisible()

    await page.getByRole('button', { name: 'Log self-assessment' }).click()
    await expect.poll(() => captured.length).toBeGreaterThan(1)
    expect(captured[captured.length - 1]).toMatchObject({
      event_type: 'self_assessment', payload: { confidence: 3 },
    })
  })
})
