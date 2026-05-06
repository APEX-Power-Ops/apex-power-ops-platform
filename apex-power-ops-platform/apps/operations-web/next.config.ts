import path from 'node:path'
import { fileURLToPath } from 'node:url'

import type { NextConfig } from 'next'

const projectRoot = path.dirname(fileURLToPath(import.meta.url))
const workspaceRoot = path.resolve(projectRoot, '..', '..')
const repoRoot = path.resolve(workspaceRoot, '..')
const mutationSeamBaseUrl =
  process.env.MUTATION_SEAM_BASE_URL?.trim().replace(/\/+$/, '') || 'http://localhost:8000'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: repoRoot,
  turbopack: {
    root: repoRoot,
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/reads/:path*',
        destination: `${mutationSeamBaseUrl}/api/v1/reads/:path*`,
      },
      {
        source: '/api/v1/schedule/:path*',
        destination: `${mutationSeamBaseUrl}/api/v1/schedule/:path*`,
      },
      {
        source: '/api/v1/mutations/:path*',
        destination: `${mutationSeamBaseUrl}/api/v1/mutations/:path*`,
      },
    ]
  },
}

export default nextConfig