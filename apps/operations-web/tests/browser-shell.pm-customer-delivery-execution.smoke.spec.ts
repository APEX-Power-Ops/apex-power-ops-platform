import { expect, test } from '@playwright/test'

test('pm customer delivery execution route orchestrates one governed seam request and readback refresh', async ({ page }) => {
  const mutationRequests: Array<{ authorization?: string; body: any }> = []
  let readCount = 0

  await page.route('**/api/v1/reads/temp-power-customer-delivery-event-status', async (route) => {
    readCount += 1

    const body =
      readCount === 1
        ? {
            status: 'no_customer_delivery_event_record',
            preview_review_lineage_match: false,
            delivery_proof_review_lineage_match: false,
            finance_authority: 'not_admitted',
            source_writeback_authority: 'not_admitted',
            customer_billing_delivery_authority: 'not_admitted',
          }
        : {
            status: 'customer_delivery_event_recorded_current_match',
            latest_customer_delivery_event_id: 'temp-power-delivery-event-0001',
            latest_delivered_at_utc: '2026-05-18T23:45:00Z',
            latest_delivery_proof_type: 'EMAIL_RECEIPT',
            latest_delivery_proof_ref: 'receipt://temp-power/2026-05-18/email-receipt-0001',
            preview_review_lineage_match: true,
            delivery_proof_review_lineage_match: true,
            finance_authority: 'not_admitted',
            source_writeback_authority: 'not_admitted',
            customer_billing_delivery_authority: 'not_admitted',
          }

    await route.fulfill({ json: body })
  })

  await page.route('**/api/v1/mutations/temp-power-customer-delivery-events', async (route) => {
    mutationRequests.push({
      authorization: route.request().headers()['authorization'],
      body: route.request().postDataJSON(),
    })

    await route.fulfill({
      json: {
        status: 'accepted',
        mutation_id: 'mut-347-0001',
        entity_id: 'temp-power-delivery-event-0001',
        entity_type: 'pm_customer_delivery_event',
        action_type: 'persist_temp_power_customer_delivery_event',
        audit_event_id: 'audit-347-0001',
        new_state: {
          customer_delivery_event_id: 'temp-power-delivery-event-0001',
          customer_delivery_status: 'DELIVERED_AND_PROOF_ATTACHED',
          execution_storage_status: 'accepted_for_customer_delivery_event_storage',
          finance_export_recorded: false,
          source_writeback_recorded: false,
          customer_billing_delivery_recorded: false,
        },
      },
    })
  })

  const response = await page.goto('/pm-review/customer-delivery-execution', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /PM customer delivery execution now has an admitted orchestration route/i })).toBeVisible()
  await expect(page.getByText(/no_customer_delivery_event_record/i)).toBeVisible()
  await expect(page.getByText(/Boundaries remain blocked: finance export, source writeback, customer billing delivery/i)).toBeVisible()

  await page.getByRole('button', { name: /Execute customer delivery event/i }).click()

  await expect(page.getByText(/accepted_for_customer_delivery_event_storage/i)).toBeVisible()
  await expect(page.getByText(/customer_delivery_event_recorded_current_match/i)).toBeVisible()
  await expect(page.getByText(/temp-power-delivery-event-0001/i).first()).toBeVisible()

  expect(readCount).toBeGreaterThanOrEqual(2)
  expect(mutationRequests).toHaveLength(1)

  const mutation = mutationRequests[0]
  const tokenPayload = JSON.parse(Buffer.from((mutation.authorization || '').replace(/^Bearer /, ''), 'base64').toString('utf8'))
  expect(tokenPayload.actor_role).toBe('pm')
  expect(mutation.body.idempotency_key).toBeTruthy()
  expect(Number.isNaN(Date.parse(mutation.body.client_timestamp))).toBeFalsy()
  expect(mutation.body).toMatchObject({
    mutation_class: 'C',
    action_type: 'persist_temp_power_customer_delivery_event',
    entity_id: 'temp-power-delivery-event-0001',
    payload: {
      project_id: 'pm-import-project-miner-temp-power',
      candidate_id: 'pm-import-candidate-miner-temp-power',
      source_fingerprint: 'e111fdbe934bf9de07ed24c1',
      customer_delivery_event_id: 'temp-power-delivery-event-0001',
      delivery_channel: 'CONTROLLED_EMAIL',
      execution_method: 'CONTROLLED_EMAIL_OPERATOR_SEND',
      customer_delivery_status: 'DELIVERED_AND_PROOF_ATTACHED',
      proof_recorded_at_utc: '2026-05-18T23:45:00Z',
    },
    reason:
      'Persist admitted Temp Power customer-facing delivery execution event only; finance, source writeback, and customer billing delivery remain blocked.',
    source: 'online',
  })
  expect(mutation.body.payload.delivery_artifact_refs).toEqual(['delivery://temp-power/2026-05-18/email-package-0001'])
})