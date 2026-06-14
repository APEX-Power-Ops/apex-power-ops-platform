// The single source of truth for the breaker CLASS carried by every breaker-scoped ETU
// fetch (both cross-filter cascades, the SST bridge, and the alt-trip lookup).
//
// breaker_id / breaker_style_id are PER-CLASS serials that COLLIDE across ICCB / MCCB / PCB
// (the #23 / DURABLE cross-class id collision). A breaker-scoped request that omits the
// class therefore lets a classless serial match a foreign-class breaker and leak its trips
// (the F02 symptom: a Square D breaker surfacing an Entelliguard "MICROLOGIC 6.0").
//
// The explicit class dropdown wins; when the operator skipped it, fall back to the class
// DERIVED from the chosen breaker. Routing all four call sites through this one resolver is
// what keeps them from drifting apart again (the bug was two sites with the fallback and two
// without).
export function effectiveBreakerClass(
  explicitClass: string | null | undefined,
  derivedClass: string | null | undefined,
): string | null {
  return explicitClass || derivedClass || null
}
