/**
 * SC3 field-facing terminology helpers (task #129).
 *
 * The served TerminologyBlock (from /settings, backed by the governed
 * tcc.field_terminology dictionary) is preferred; every helper falls back to
 * the RULED vocabulary baked in here (operator red-line 2026-06-11: Q2 db
 * badge = MFR, Q3 unsupported = N/A, Q5 "Test Current", plug = "Rating plug
 * (In)" — the Plug-(Ir) mislabel fix), so the page reads correctly even when
 * the block is absent (fail-open serving).
 */

import type { TerminologyBlock, TerminologyElementDisplay } from './breaker-resources'

/** Ruled trust-badge words (mirror the dictionary's '*' trust rows). */
export const TRUST_BADGE_FALLBACK: Record<string, string> = {
  'pickup.db': 'MFR',
  'delay.db': 'MFR',
  'delay.verify': 'VERIFY',
  'delay.unsupported': 'N/A',
}

export function trustBadgeWord(key: keyof typeof TRUST_BADGE_FALLBACK | string, term?: TerminologyBlock | null): string {
  return term?.trust?.[key]?.badge ?? TRUST_BADGE_FALLBACK[key] ?? String(key)
}

export function trustTitle(key: string, reason: string | null | undefined, term?: TerminologyBlock | null): string {
  // Field phrasing first; the engineering citation (trust_reason) stays as the
  // audit trail on the same tooltip.
  return [term?.trust?.[key]?.text, reason].filter(Boolean).join(' — ')
}

/** Element display: served lineage row, else the caller's built-in meta. */
export function elementDisplay(
  key: string,
  fallbackCode: string,
  fallbackLabel: string,
  term?: TerminologyBlock | null,
): TerminologyElementDisplay {
  const served = term?.elements?.[key]
  if (served) {
    return {
      code: served.code || fallbackCode,
      label: served.label || fallbackLabel,
      symbol: served.symbol ?? null,
      note: served.note ?? null,
    }
  }
  return { code: fallbackCode, label: fallbackLabel, symbol: null, note: null }
}

/** The plug selector label — "Rating plug (In)": the plug sets In; Ir is the
 *  long-time dial × In (MICROLOGIC-6.0A.md; live 3833 plug 400–1200 A). */
export function plugLabel(term?: TerminologyBlock | null): string {
  return term?.plug_label ?? 'Rating plug (In)'
}

/** Q5 ruling: the test-point wording is "Test Current". */
export function testCurrentLabel(term?: TerminologyBlock | null): string {
  return term?.test_current_label ?? 'Test Current'
}
