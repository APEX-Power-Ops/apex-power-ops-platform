export type PmRouteParams = Record<string, string | number | null | undefined>

export function buildPmRoute(
  path: string,
  params: PmRouteParams,
) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return
    }

    query.set(key, String(value))
  })

  const nextQuery = query.toString()
  return nextQuery ? `${path}?${nextQuery}` : path
}

export function buildPmReturnContext(
  path: string,
  currentParams: PmRouteParams,
  returnLabel: string,
) {
  return {
    returnTo: buildPmRoute(path, currentParams),
    returnLabel,
  }
}

export function parsePmRoute(target: string | null | undefined) {
  if (!target) {
    return null
  }

  try {
    return new URL(target, 'http://apex.local')
  } catch {
    return null
  }
}