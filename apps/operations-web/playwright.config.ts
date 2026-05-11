import { defineConfig } from '@playwright/test'

const hostedBaseUrl = process.env.OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL?.trim()
const port = Number(process.env.OPERATIONS_WEB_BROWSER_SMOKE_PORT ?? '3030')
const nextBin = './node_modules/next/dist/bin/next'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  reporter: 'list',
  timeout: 30_000,
  use: {
    baseURL: hostedBaseUrl || `http://127.0.0.1:${port}`,
    headless: true,
  },
  webServer: hostedBaseUrl
    ? undefined
    : {
        command: `"${process.execPath}" ${nextBin} start -p ${port}`,
        cwd: __dirname,
        env: {
          ...process.env,
          NEXT_PUBLIC_SUPABASE_URL:
            process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://example.supabase.co',
          NEXT_PUBLIC_SUPABASE_ANON_KEY:
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? 'browser-smoke-anon-key',
          NEXT_PUBLIC_CONTROL_PLANE_BASE_URL:
            process.env.NEXT_PUBLIC_CONTROL_PLANE_BASE_URL ?? 'http://127.0.0.1:8010',
        },
        reuseExistingServer: !process.env.CI,
        stdout: 'pipe',
        stderr: 'pipe',
        timeout: 60_000,
      },
})