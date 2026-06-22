export const meta = {
  name: 'irp-grounded-audit',
  description: 'IRP Audit mode (grounded): parallel source-grounded probes of an artifact -> adversarial regression hunt -> final verdict memo. args: { subject, constraints, groundingNote, depth: Light|Standard|Deep, probes?: [{key, angle}] }',
  phases: [{ title: 'Probe' }, { title: 'Assess' }],
}

const A = args || {}
const subject = A.subject || 'the artifact'
const CONSTRAINTS = A.constraints || ''
const GROUND = A.groundingNote || 'Ground EVERY claim in authoritative source (code / DB / spec). Cite the specific object behind each claim. If you cannot verify something, list it under "unverified" rather than asserting it.'
const depth = A.depth || 'Standard'
const nProbes = depth === 'Deep' ? 4 : depth === 'Light' ? 1 : 3
const probes = (A.probes && A.probes.length)
  ? A.probes
  : Array.from({ length: nProbes }, (_, i) => ({ key: `probe-${i + 1}`, angle: `Independently audit "${subject}" for defects (lens #${i + 1}): what is wrong, missing, unsafe, or unverifiable?` }))

const P = {
  type: 'object', required: ['facet', 'findings', 'unverified'], additionalProperties: false,
  properties: {
    facet: { type: 'string' },
    findings: { type: 'array', items: {
      type: 'object', required: ['what', 'severity', 'evidence'], additionalProperties: false,
      properties: { what: { type: 'string' }, severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] }, evidence: { type: 'string' } },
    } },
    unverified: { type: 'array', items: { type: 'string' } },
  },
}
const ADV = {
  type: 'object', required: ['regressions', 'missed', 'verdict'], additionalProperties: false,
  properties: {
    regressions: { type: 'array', items: {
      type: 'object', required: ['what', 'severity'], additionalProperties: false,
      properties: { what: { type: 'string' }, severity: { type: 'string', enum: ['fatal', 'important', 'minor'] } },
    } },
    missed: { type: 'array', items: { type: 'string' }, description: 'what the probes missed or asserted unverified' },
    verdict: { type: 'string' },
  },
}

phase('Probe')
const found = (await parallel(probes.map(p => () =>
  agent(`${CONSTRAINTS}\n\n${GROUND}\n\nProbe "${p.key}": ${p.angle}\n\nReturn the structured object.`,
    { label: `probe:${p.key}`, phase: 'Probe', schema: P })
))).filter(Boolean)

phase('Assess')
const adv = await agent(
  `${CONSTRAINTS}\n\n${GROUND}\n\nYou are an adversarial reviewer. Here are the grounded probe findings for "${subject}". Try to break the artifact FURTHER: what regresses, what did the probes miss, what is asserted-but-unverified? Re-check against source where you can. Default to flagging.\n\nPROBES:\n${JSON.stringify(found, null, 2)}\n\nReturn the structured verdict.`,
  { label: 'regression-hunt', phase: 'Assess', schema: ADV })

const final = await agent(
  `You are the lead reviewer. Produce the IRP audit memo as markdown starting with an H1:\n# ${subject} — Grounded Audit\n## Verdict\n## Findings (severity + grounded evidence)\n## Regression risks (from the adversarial pass)\n## Unverified / needs source\n## Operator decisions to surface (with leans)\nReturn ONLY markdown from the H1.\n\nPROBES:\n${JSON.stringify(found, null, 2)}\n\nADVERSARIAL:\n${JSON.stringify(adv, null, 2)}`,
  { label: 'final', phase: 'Assess' })

return final
