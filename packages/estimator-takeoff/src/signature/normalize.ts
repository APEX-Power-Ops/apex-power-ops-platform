import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, BreakerSignature, Coolant, Mounting, MountingBasis, MvType, RelayRole, RelaySignature, RelayTechnology, GfpSignature, TransformerSignature, TripFunction, VoltageBasis, InstrumentTransformerSignature, ItxPackaging, ItxPackagingEvidence, ItxType, SwitchType, SwitchSignature } from './types'
import type { OperatorQuestion, OperatorQuestionCode } from '../buckets/types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(?<!\d)(\d{2,6})\s*AF\s*\/\s*(\d{2,6})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
const NON_BREAKER = /\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

const TRANSFORMER_DEVICE = /\b(XFMR|transformer|dry.?type|pad.?mount|oil.?filled)\b/i
const KVA_RATING = /(?<!\w)\d+(?:\.\d+)?\s*kVA\b/i

const RELAY_DEVICE = /\b(protective\s+relay|relay|SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom)\b/i
// STANDALONE GFP device NOUNS only. Deliberately does NOT match a bare ANSI ground function (50G/51G/64),
// the trip-function letter G, bare "ground fault protection" (function name), "ground fault test", or "per 7.14".
const GFP_DEVICE = /\b(GFPE?|GFR|ground[\s-]?fault\s+(relay|sensor|monitor|module|system|device|unit)|ground[\s-]?fault\s+protection\s+(system|device|unit|relay|module|panel))\b/i
const ANSI_FN = /\b(2[1-7]|32|37|38|40|46N?|47|49[RT]?|50N?|51N?|55|59|60|63|64|67|79|81|86|87[TBGN]?)\b/gi
const INSTRUMENT_TX_DEVICE = /\b(current\s+transformer|potential\s+transformer|voltage\s+transformer|coupling[\s-]?capacitor(\s+voltage\s+transformer)?|CCVT|instrument\s+transformer)\b/i
const INSTRUMENT_TX_ABBR = /\b(CT|PT|VT)\b/i
const INSTRUMENT_TAG = /^(CT|PT|VT|CCVT)[-_ ]?\w*$/i

// --- Switch / disconnect family (NETA 7.5) ---
// Overload families EXCLUDED FIRST (T3): "switch" appears in switchboard/switchgear (7.1 assemblies),
// transfer switch (7.18/22), circuit switcher (7.3). None are 7.5 switches.
const SWITCH_EXCLUDE = /\b(circuit\s+switcher|transfer\s+switch|switchgear|switchboard)\b/i
// COMPOUND switch-device anchors - NEVER the bare token "switch".
const SWITCH_DEVICE = /\b(disconnect(\s+switch)?|fus(ed|ible)\s+switch|safety\s+switch|load[\s-]?break\s+switch|LBS|isolat(ion|ing)\s+switch|knife\s+switch|air\s+switch|oil\s+switch|SF6\s+switch|vacuum\s+switch|cutout|non[\s-]?fused\s+disconnect)\b/i
// D3 clarification (operator-ratified): bare "switch"/"DISC" do NOT count, but a switch-ish NOUN paired with an
// explicit CONSTRUCTION medium/type token (EITHER ORDER) IS a compound switch anchor - so "Switch (SF6)",
// "Switch, SF6", "DISC SF6", "Switch (Vacuum)", "Switch MV - Motor Operated" recognize (closing the misprice where
// a shared medium [SF6/vacuum/air in BREAKER_HINT] otherwise carried a switch label to the breaker path). Full
// "disconnect" and the medium+"switch" compounds already count via SWITCH_DEVICE. Exclusions + conflict guard still run.
const SWITCH_NOUN = /\b(switch|disc)\b/i
const SWITCH_CONSTRUCTION = /\b(SF6|vacuum|oil|air|pad[\s-]?mount|vista|cutout|fus(ed|ible)|motor[\s-]?operated|M\.?O\.?)\b/i
// The UNAMBIGUOUS breaker subset for the switch-local conflict guard - DELIBERATELY excludes the shared
// vacuum/SF6/air-frame medium tokens (those are switch construction evidence, not conflict signals).
const SWITCH_BREAKER_CONFLICT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i
// A single numbered frame/trip token (catches 800AF or 800AT even WITHOUT the full FRAME_TRIP pair).
const SWITCH_FRAME_TRIP = /\b\d{2,6}\s*A[FT]\b/i
// A breaker trip-function descriptor on a switch row = conflict (mirrors parseFunctions' L(SIGE) shape).
// REQUIRES >=2 function letters after L (lookahead `[SIGE]{2}`): a genuine descriptor is the LSI/LSIG family,
// so "LSIG" matches while a bare 2-char TAG prefix carried into the raw (LS-1 / LG-2 / LI-7 / LE-3, where the
// delimiter satisfies \b after a single SIGE letter) does NOT - avoiding the false-positive that mis-flagged a
// legitimate disconnect as switch_parent_conflict. The ordered (S?)(I?)(G?)(E?) groups + \b still spare LBS
// (L+B), LV (L+V), and English words like LESS/LIGHT.
const SWITCH_TRIP_FN = /\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i
// The non-fused attribute - consumed ONLY when a real anchor is present (looksLikeSwitch gates it).
// Split into two strengths so parseFused can rank them: explicit NEGATED wording (non|un x fused|fusible - the
// whole negated-fused class) is authoritative, while the bare NF ABBREVIATION is weaker than explicit fused
// wording (so a fused device whose TAG starts with NF, e.g. "NF-1 Fused Disconnect", is not misread as non-fused).
const NEGATED_FUSED = /\b(non|un)[\s-]?fus(ed|ible)\b/i
const NF_ABBR = /\bN\.?F\.?\b/i
// PLAIN continuous amps ONLY: the \bA\b boundary means 800AF / 800AT do NOT match (AF/AT can never be amps).
const SWITCH_AMP = /(?<!\d)(\d{2,6})\s*A\b/i

// Transformer-protection accessory relays (pressure/temperature/Buchholz/gas) are NOT standalone
// protective-relay DEVICES the firm prices. Exclude them from token-based recognition so a plain
// "FAULT PRESSURE RELAY" does not become a priced relay (an explicit candidateKind:'relay' still wins).
const RELAY_ACCESSORY = /\b((sudden|fault)\s*pressure|pressure|buchholz|gas\s*accumulator)\s*relay\b/i
// A relay MODEL family is a strong device anchor (device-first); it outranks a transformer text token.
const RELAY_MODEL = /\b(SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom)\b/i

function looksLikeTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'relay') return false                  // relay producer signal wins over XFMR text
  if (x.candidateKind === 'instrument_transformer') return false   // explicit instrument producer signal yields
  if (x.candidateKind === 'switch') return false                   // explicit switch producer signal yields (a pad-mount Vista SWITCH must set candidateKind:'switch' to escape pad-mount transformer text)
  if (INSTRUMENT_TX_DEVICE.test(x.raw)) return false               // instrument device noun is NOT a power transformer (additive; no kVA/coolant requirement)
  if (x.candidateKind === 'transformer') return true
  // NOTE: a TEXT-based switch yield was deliberately NOT added here. "pad mount" lives in BOTH TRANSFORMER_DEVICE
  // and parseCoolant, so a blanket `isSwitchAnchored -> yield` stole real transformer rows that merely mention an
  // accessory disconnect (e.g. "1500KVA DRY-TYPE XFMR FUSED DISCONNECT"). Bare-text Pad-Mount-Vista disambiguation
  // is the R1/SME anchor-coverage follow-up; producer candidateKind:'switch' is the escape hatch in the meantime.
  // A relay MODEL + tag outranks a transformer text token (device-first) ONLY when the row lacks
  // strong transformer evidence. A real transformer (kVA rating or a coolant/construction token) that
  // merely MENTIONS a relay model must stay a transformer - never silently reclassified as a relay.
  if (RELAY_MODEL.test(x.raw) && x.tag !== undefined && x.tag.length > 0
      && !KVA_RATING.test(x.raw) && parseCoolant(x.raw) === 'unknown') return false
  if (TRANSFORMER_DEVICE.test(x.raw)) return true
  // FIX 4: kVA-rating fallback must not steal NON_BREAKER rows (UPS, PDU, etc. can carry kVA ratings).
  // A real transformer device token (XFMR/transformer/dry-type/pad-mount/oil-filled) already recognizes above.
  // kVA-breaker guard: also exclude a breaker label that merely carries a kVA value (e.g. a main feeding a 500kVA xfmr) via !looksLikeBreaker.
  return KVA_RATING.test(x.raw) && (x.tag !== undefined && x.tag.length > 0) && !NON_BREAKER.test(x.raw) && !looksLikeBreaker(x.raw)
}

function looksLikeBreaker(raw: string): boolean {
  return BREAKER_HINT.test(raw) || FRAME_TRIP.test(raw)
}

function parseFunctions(raw: string): TripFunction[] {
  const ft = raw.match(FRAME_TRIP)
  const region = ft && ft.index !== undefined ? raw.slice(ft.index + ft[0].length) : raw
  const m = region.match(/\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i)
  if (!m) return []
  const tok = m[0].toUpperCase()
  const out: TripFunction[] = ['L']
  if (tok.includes('S')) out.push('S')
  if (tok.includes('I')) out.push('I')
  if (tok.includes('G') || tok.includes('E')) out.push('G')
  return out
}

function parseMounting(raw: string): Mounting {
  if (/\bMCB\b|panelboard/i.test(raw)) return 'panelboard'
  if (/molded\s*case|MCCB/i.test(raw)) return 'molded_case'
  if (/insulated\s*case|\bICCB\b/i.test(raw)) return 'insulated_case'
  if (/electrically\s*operated|\(EO\)/i.test(raw)) return 'electrically_operated'
  if (/draw.?out|\bD\/O\b|\(DO\)/i.test(raw)) return 'draw_out'
  return 'unknown'
}

function parseMvType(raw: string): MvType {
  if (/vacuum|\bVCB\b/i.test(raw)) return 'vacuum'
  if (/SF6/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/air\s*frame/i.test(raw)) return 'air_frame'
  return 'unknown'
}

function resolveMounting(
  x: ExtractedApparatus, frameA: number | undefined, functions: TripFunction[],
): { mounting: Mounting; basis: MountingBasis; conflict: boolean } {
  const textMount = parseMounting(x.raw)
  if (x.mountingHint) {
    const conflict = textMount !== 'unknown' && textMount !== x.mountingHint
    return { mounting: x.mountingHint, basis: 'hint', conflict }
  }
  if (textMount !== 'unknown') return { mounting: textMount, basis: 'text', conflict: false }
  const hasG = functions.includes('G')
  if (frameA !== undefined && frameA >= 800 && hasG) return { mounting: 'draw_out', basis: 'estimating_baseline', conflict: false }
  return { mounting: 'unknown', basis: 'none', conflict: false }
}

// Transformer attribute parsers -- text-only, fail-closed.
// kVA vs kV: the word boundary after 'kVA' ensures '30KVA' matches but '30kV' does not.
function parseKva(raw: string): number | undefined {
  const m = raw.match(/(?<!\w)(\d+(?:\.\d+)?)\s*kVA\b/i)
  return m ? Number(m[1]) : undefined
}

function parseCoolant(raw: string): Coolant {
  if (/\b(oil.?filled|pad.?mount|liquid|mineral\s*oil)\b/i.test(raw)) return 'liquid'
  if (/\b(dry.?type|\bAA\b|ventilated|cast\s*resin)\b/i.test(raw)) return 'dry'
  return 'unknown'
}

function parsePadMount(raw: string): boolean {
  return /\bpad.?mount\b/i.test(raw)
}

function parseLtc(raw: string): boolean {
  return /\b(LTC|load\s*tap\s*changer|on.?load\s*tap)\b/i.test(raw)
}

function looksLikeRelay(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'relay') return true                  // explicit producer signal wins
  if (RELAY_ACCESSORY.test(x.raw)) return false                 // transformer accessory, not a priced relay device
  return RELAY_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}

// True when the raw carries a switch anchor under the D3 grammar: a full SWITCH_DEVICE compound, OR a switch-ish
// NOUN (bare "switch"/"DISC") paired with explicit CONSTRUCTION evidence. Exclusions are honored here so the
// breaker-fallback guard and looksLikeSwitch share ONE definition. Does NOT require a tag (the device-first tag
// gate lives in looksLikeSwitch); the breaker gate uses it tagless so a tagless medium-carrying switch label is
// never mispriced as a breaker.
function isSwitchAnchored(raw: string): boolean {
  if (SWITCH_EXCLUDE.test(raw)) return false
  return SWITCH_DEVICE.test(raw) || (SWITCH_NOUN.test(raw) && SWITCH_CONSTRUCTION.test(raw))
}

export function looksLikeSwitch(x: ExtractedApparatus): boolean {
  if (SWITCH_EXCLUDE.test(x.raw)) return false                          // T3: overload families excluded FIRST
  if (x.candidateKind === 'switch') return true                         // explicit producer signal wins
  if (x.candidateKind !== undefined) return false                       // defer to other producers (TS narrows: not 'switch' here)
  return isSwitchAnchored(x.raw) && x.tag !== undefined && x.tag.length > 0       // (compound device OR noun+construction) + tag
}

export function parseSwitchType(raw: string): SwitchType {
  if (/pad[\s-]?mount\s+vista|\bvista\b/i.test(raw)) return 'vista'
  if (/motor[\s-]?operated|\bM\.?O\.?\b/i.test(raw)) return 'motor_operated'
  if (/\bSF6\b/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/\bcutout\b/i.test(raw)) return 'cutout'
  if (/\bvacuum\b/i.test(raw)) return 'vacuum'                          // recognized; no priced ref -> gap
  if (/fus(ed|ible)/i.test(raw) && !NEGATED_FUSED.test(raw)) return 'fused_disconnect'  // NOT any negated-fused form
  if (/air\s+switch|\bopen\b/i.test(raw)) return 'open'                 // air-open switches ARE the firm "Open" refs
  return 'unknown'                                                       // generic disconnect/switch anchor -> group, no default
}

export function parseFused(raw: string): boolean | undefined {
  if (NEGATED_FUSED.test(raw)) return false            // "non-fused"/"unfused"/"non-fusible" -> non-fused (authoritative)
  if (/fus(ed|ible)/i.test(raw)) return true           // explicit "fused"/"fusible" wording beats a bare NF tag prefix
  if (NF_ABBR.test(raw)) return false                  // bare "NF" abbreviation - only when there is no explicit fused wording
  return undefined
}

export function parseAmpRating(raw: string): number | undefined {
  const m = raw.match(SWITCH_AMP)
  return m ? Number(m[1]) : undefined
}

// LOAD-BEARING standalone guard: a parent-shaped row (a breaker by frame/hint, or a NON_BREAKER device)
// carries its ground-fault burden in the PARENT ref, so it can NEVER become a GFP device - even with
// candidateKind:'gfp'. Exported for a direct unit test (the rule that prevents drift).
export function isGfpParentShape(x: ExtractedApparatus): boolean {
  return looksLikeBreaker(x.raw) || NON_BREAKER.test(x.raw)
}

function looksLikeGfp(x: ExtractedApparatus): boolean {
  if (isGfpParentShape(x)) return false                 // parent exclusion BEFORE candidateKind (non-negotiable #1)
  if (x.candidateKind === 'gfp') return true            // producer asserts a STANDALONE GFP device
  if (x.candidateKind !== undefined && x.candidateKind !== 'relay') return false  // defer to breaker/transformer producer signals; a relay row with dedicated GFP wording still becomes GFP
  return GFP_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}

function assessGfp(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // No FRAME_TRIP/conflict guard: looksLikeGfp (isGfpParentShape) already excludes any breaker-shaped row,
  // so assessGfp is only reached for a clean standalone device. The invariant is pinned by a test.
  const voltageClass = classifyVoltage(x.busVoltageV)   // MAY be undefined - GFP voltage contextual, NOT gated
  const sig: GfpSignature = {
    kind: 'gfp',
    ansiFunctions: parseAnsiFunctions(x.raw),
    voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'gfp_recognized', questions: [] }
}

function looksLikeInstrumentTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'instrument_transformer') return true
  // A relay or GFP producer signal outranks a full-noun instrument device token (A-prime negative guard):
  // a relay/GFP row that merely MENTIONS "potential transformer" / "voltage transformer" stays its real
  // family and is NOT reclassified as an instrument transformer. Also applies when RELAY_DEVICE matches
  // the raw with a non-instrument-shaped tag (e.g. "SEL-351 RELAY POTENTIAL TRANSFORMER" tag "REL-1").
  if (x.candidateKind === 'relay' || x.candidateKind === 'gfp') return false
  if (RELAY_DEVICE.test(x.raw) && x.tag !== undefined && !INSTRUMENT_TAG.test(x.tag)) return false
  if (INSTRUMENT_TX_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0) return true   // full noun + any tag
  if (INSTRUMENT_TX_ABBR.test(x.raw) && x.tag !== undefined && INSTRUMENT_TAG.test(x.tag)) return true  // bare abbr needs instrument-shaped tag (A-prime)
  return false
}

function parseItxType(raw: string, tag?: string): ItxType | undefined {
  if (/\b(CCVT|coupling[\s-]?capacitor)\b/i.test(raw) || (tag !== undefined && /^CCVT/i.test(tag))) return 'ccvt'
  if (/\b(potential\s+transformer|voltage\s+transformer|PT|VT)\b/i.test(raw) || (tag !== undefined && /^(PT|VT)/i.test(tag))) return 'vt'
  if (/\b(current\s+transformer|CT)\b/i.test(raw) || (tag !== undefined && /^CT/i.test(tag))) return 'ct'
  return undefined   // NO CT/PT/VT/CCVT type token (e.g. candidateKind-only row with an opaque tag/ratio) -> fail closed; NEVER fabricate 'ct'
}

function parsePackaging(raw: string): { packaging: ItxPackaging; packagingEvidence: ItxPackagingEvidence; phaseCount?: number } {
  if (/\bset\s+of\s+3\b/i.test(raw)) return { packaging: 'set', packagingEvidence: 'set_of_3', phaseCount: 3 }
  if (/\b3\s*(?:phase|ph|-phase)\b/i.test(raw) || /\b3\s*x\b/i.test(raw) || /\(3\)/.test(raw)) return { packaging: 'set', packagingEvidence: 'three_phase', phaseCount: 3 }
  if (/\bset\b/i.test(raw)) return { packaging: 'set', packagingEvidence: 'set_token' }
  if (/\bindividual\b/i.test(raw)) return { packaging: 'individual', packagingEvidence: 'individual_token' }   // explicit individual token (P2-b) -> the individual provisional default
  return { packaging: 'unknown', packagingEvidence: 'none' }
}

function parseRatio(raw: string): string | undefined {
  const m = raw.match(/\b\d+\s*:\s*\d+\b/)
  return m ? m[0].replace(/\s+/g, '') : undefined
}

function assessInstrumentTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // Conflict guards FIRST (instrument routes before breaker/NON_BREAKER): a misrouted parent surfaces a
  // question, never a silent instrument scope_pending.
  if (looksLikeBreaker(x.raw) || NON_BREAKER.test(x.raw)) {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_parent_conflict',
      questions: [q(x, 'Label names an instrument transformer but the row is breaker/parent-shaped (frame/trip or a parent-device token) - confirm device type before counting.', 'instrument_transformer_parent_conflict')] }
  }
  if (KVA_RATING.test(x.raw) || parseCoolant(x.raw) !== 'unknown') {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_power_conflict',
      questions: [q(x, 'Label names an instrument transformer but carries a power-transformer signal (kVA/coolant) - confirm device type before counting.', 'instrument_transformer_power_conflict')] }
  }
  const itxType = parseItxType(x.raw, x.tag)
  if (itxType === undefined) {
    // Flagged as an instrument transformer (candidateKind or context) but no CT/PT/VT/CCVT type token -> fail closed.
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_type_unparsed',
      questions: [q(x, 'Row is flagged as an instrument transformer but names no CT/PT/VT/CCVT type - confirm the instrument-transformer type before counting.', 'instrument_transformer_type_unparsed')] }
  }
  const pk = parsePackaging(x.raw)
  const sig: InstrumentTransformerSignature = {
    kind: 'instrument_transformer', itxType,
    packaging: pk.packaging, packagingEvidence: pk.packagingEvidence, phaseCount: pk.phaseCount,
    ratio: parseRatio(x.raw),
    voltageClass: classifyVoltage(x.busVoltageV), voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag, source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'instrument_transformer_recognized', questions: [] }
}

function parseRelayTechnology(raw: string): RelayTechnology {
  if (/\b(SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom|microprocessor|uP)\b/i.test(raw)) return 'microprocessor'
  if (/\b(electromechanical|EM|solid.?state)\b/i.test(raw)) return 'electromechanical_solid_state'
  return 'unknown'
}

function parseAnsiFunctions(raw: string): string[] {
  const out = new Set<string>()
  for (const m of raw.matchAll(ANSI_FN)) out.add(m[1]!.toUpperCase())
  return [...out]
}

function parseRelayModel(raw: string): string | undefined {
  const m = raw.match(/\b(SEL-?\d{2,4}[A-Z]?|multilin\s*\w+|beckwith\s*\w+|basler\s*\w+|micom\s*\w+)\b/i)
  return m ? m[0] : undefined
}

function deriveRole(ansi: string[], raw: string, tech: RelayTechnology): RelayRole {
  const has = (n: string) => ansi.includes(n)
  // Complex / multi-element roles first (these take their tier even on legacy technology).
  if (has('87T') || /(transformer|XFMR)\s+diff/i.test(raw)) return 'differential'
  if (has('87B') || /\bbus\b/i.test(raw)) return 'bus_differential'
  if (has('87')) return 'differential'
  if (/generator/i.test(raw) || (has('40') && (has('32') || has('46')))) return 'generator'
  if (has('21') || /\b(line|distance)\b/i.test(raw)) return 'line'
  if (/motor/i.test(raw) || (has('49') && has('50') && has('51'))) return 'motor'
  if (/multi.?function/i.test(raw) && /meter/i.test(raw)) return 'multifunction_meter'
  // Legacy single-function EM/solid-state -> the cheap electromechanical tier (before the generic feeder/OC roles).
  if (tech === 'electromechanical_solid_state' && ansi.length <= 1) return 'electromechanical'
  if (/feeder/i.test(raw)) return 'feeder'
  if (has('50') || has('51') || /overcurrent/i.test(raw)) return 'overcurrent'
  return 'unknown'
}

function assessRelay(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  if (FRAME_TRIP.test(x.raw)) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'relay_breaker_conflict',
      questions: [q(x, 'Label names a relay but carries a breaker frame/trip rating - confirm device type before counting.', 'relay_breaker_conflict')],
    }
  }
  const ansiFunctions = parseAnsiFunctions(x.raw)
  const technology = parseRelayTechnology(x.raw)
  const role = deriveRole(ansiFunctions, x.raw, technology)
  const voltageClass = classifyVoltage(x.busVoltageV)   // MAY be undefined - relay voltage is contextual, NOT gated
  const sig: RelaySignature = {
    kind: 'relay', technology, ansiFunctions, role,
    model: parseRelayModel(x.raw),
    voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'relay_recognized', questions: [] }
}

export type AssessmentCode =
  | 'classified'
  | 'transformer_recognized'
  | 'transformer_breaker_conflict'
  | 'transformer_scope_pending'
  | 'transformer_catalog_gap'
  | 'transformer_attrs_unparsed'
  | 'relay_recognized'
  | 'relay_breaker_conflict'
  | 'gfp_recognized'
  | 'instrument_transformer_recognized'
  | 'instrument_transformer_parent_conflict'
  | 'instrument_transformer_power_conflict'
  | 'instrument_transformer_type_unparsed'
  | 'non_breaker_excluded'
  | 'non_breaker_carries_rating'
  | 'missing_voltage'
  | 'unrecognized_apparatus_row'
  | 'switch_recognized'
  | 'switch_parent_conflict'

export interface ApparatusAssessment {
  signature: ApparatusSignature | null
  questions: OperatorQuestion[]
  isBreakerShaped: boolean
  assessmentCode: AssessmentCode
}

function q(x: ExtractedApparatus, question: string, code: OperatorQuestionCode): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})`, code }
}

// Transformer assessor with full attribute parsing (kVA, coolant, pad-mount, LTC).
// Fail-closed: if kVA AND coolant are both absent -> transformer_attrs_unparsed question.
function assessTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'missing_voltage',
      questions: [q(x, 'Looks like a transformer but has no associated bus voltage - supply voltage to classify.', 'missing_voltage')],
    }
  }

  const kvaRating = parseKva(x.raw)
  const coolant = parseCoolant(x.raw)
  const padMount = parsePadMount(x.raw)
  const ltc = parseLtc(x.raw)

  // Fail-closed: if neither kVA nor coolant can be determined, ask the operator.
  if (kvaRating === undefined && coolant === 'unknown') {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'transformer_attrs_unparsed',
      questions: [q(x, 'Transformer recognized but kVA rating and coolant type could not be parsed - supply kVA and coolant (dry/liquid) to continue.', 'transformer_attrs_unparsed')],
    }
  }

  const sig: TransformerSignature = {
    kind: 'transformer', voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    kvaRating, coolant, padMount, ltc, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'transformer_recognized', questions: [] }
}

function assessSwitch(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // CONFLICT GUARD FIRST (switch routes before the breaker fallback): a misrouted parent surfaces a question,
  // never a silent switch scope_pending and never suppressing a real breaker. Keyed on the UNAMBIGUOUS breaker
  // subset + full pair + single AF/AT token + trip functions + NON_BREAKER - NOT the shared SF6/vacuum/air medium.
  if (SWITCH_BREAKER_CONFLICT.test(x.raw) || FRAME_TRIP.test(x.raw) || SWITCH_FRAME_TRIP.test(x.raw)
      || SWITCH_TRIP_FN.test(x.raw) || NON_BREAKER.test(x.raw)) {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'switch_parent_conflict',
      questions: [q(x, 'Label names a switch/disconnect but the row carries a breaker signal (frame/trip, trip functions, or a breaker/parent token) - confirm device type before counting.', 'switch_parent_conflict')] }
  }
  const sig: SwitchSignature = {
    kind: 'switch',
    switchType: parseSwitchType(x.raw),
    fused: parseFused(x.raw),
    ampRating: parseAmpRating(x.raw),
    voltageClass: classifyVoltage(x.busVoltageV), voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag, source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'switch_recognized', questions: [] }
}

// PRIVATE -- the basis-taking core. NOT exported.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  if (looksLikeInstrumentTransformer(x)) {
    return assessInstrumentTransformer(x, voltageBasis)
  }

  if (looksLikeTransformer(x)) {
    if (FRAME_TRIP.test(x.raw)) {
      return {
        signature: null, isBreakerShaped: false, assessmentCode: 'transformer_breaker_conflict',
        // FIX 5: use 'transformer_breaker_conflict' as the OperatorQuestionCode (now valid in the union)
        questions: [q(x, 'Label names a transformer but carries a breaker frame/trip rating - confirm device type before counting.', 'transformer_breaker_conflict')],
      }
    }
    return assessTransformer(x, voltageBasis)
  }

  if (looksLikeGfp(x)) {
    return assessGfp(x, voltageBasis)
  }

  if (looksLikeRelay(x)) {
    return assessRelay(x, voltageBasis)
  }

  if (looksLikeSwitch(x)) {
    return assessSwitch(x, voltageBasis)
  }

  if (NON_BREAKER.test(x.raw)) {
    if (FRAME_TRIP.test(x.raw)) {
      return { signature: null, isBreakerShaped: false, questions: [q(x, 'Label names a non-breaker device (ATS/MTS/SPD/etc.) but carries a breaker frame/trip rating - confirm device type before counting.', 'non_breaker_carries_rating')], assessmentCode: 'non_breaker_carries_rating' }
    }
    return { signature: null, questions: [], isBreakerShaped: false, assessmentCode: 'non_breaker_excluded' }
  }
  // ROOT guard for the shared-medium misprice class: a SWITCH-anchored row must NEVER be claimed by the breaker
  // fallback, even when it carries a shared medium (vacuum/SF6/air) that BREAKER_HINT matches. looksLikeSwitch
  // requires a tag (device-first), so a TAGLESS "Vacuum Switch"/"Switch (SF6)" would otherwise fall through here and
  // be priced as a breaker; isSwitchAnchored (full SWITCH_DEVICE compound OR the noun+construction grammar) forces it
  // to unrecognized_apparatus_row (fail-closed) instead. An explicit candidateKind:'breaker' still builds a breaker.
  if (x.candidateKind !== 'breaker' && (!looksLikeBreaker(x.raw) || isSwitchAnchored(x.raw))) return { signature: null, questions: [], isBreakerShaped: false, assessmentCode: 'unrecognized_apparatus_row' }

  const questions: OperatorQuestion[] = []
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    questions.push(q(x, 'Looks like a breaker but has no associated bus voltage - supply voltage to classify (LV/MV/HV).', 'missing_voltage'))
    return { signature: null, questions, isBreakerShaped: true, assessmentCode: 'missing_voltage' }
  }

  const ft = x.raw.match(FRAME_TRIP)
  const frameA = ft ? Number(ft[1]) : undefined
  const tripA = ft ? Number(ft[2]) : undefined
  const functions = parseFunctions(x.raw)

  if (voltageClass === 'LV' && !ft) {
    questions.push(q(x, 'LV breaker frame/trip rating (AF/AT) could not be parsed - verify rating.', 'lv_frame_trip_unparsed'))
  }

  let mounting: Mounting = 'unknown'
  let mountingBasis: MountingBasis = 'none'
  if (voltageClass === 'LV') {
    const r = resolveMounting(x, frameA, functions)
    mounting = r.mounting
    mountingBasis = r.basis
    if (r.conflict) {
      questions.push(q(x, `Construction hint "${x.mountingHint}" conflicts with the label text - verify breaker construction.`, 'mounting_hint_conflict'))
    }
    if (functions.length === 0 && (mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case')) {
      questions.push(q(x, 'Power-breaker trip-function descriptor (e.g. LSIG) missing - confirm functions (affects LSIG vs LS/LSI vs unmatched).', 'missing_power_functions'))
    }
  }
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined

  const basis: VoltageBasis = voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')

  const signature: BreakerSignature = {
    kind: 'breaker', voltageClass, voltageV: x.busVoltageV, voltageBasis: basis, frameA, tripA, functions,
    mounting, mountingBasis, mvType, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature, questions, isBreakerShaped: true, assessmentCode: 'classified' }
}

// PUBLIC -- one-arg only. A caller cannot supply 'asserted'; basis is derived detected/none.
export function assessApparatus(x: ExtractedApparatus): ApparatusAssessment {
  return assessCore(x)
}

// ENGINE-INTERNAL -- used by runTakeoff to pass the validated/controlled basis.
// Exported from this module for emit.ts, but DELIBERATELY NOT re-exported from src/index.ts.
export function assessResolvedApparatus(x: ExtractedApparatus, voltageBasis: VoltageBasis): ApparatusAssessment {
  return assessCore(x, voltageBasis)
}

export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  return assessApparatus(x).signature
}