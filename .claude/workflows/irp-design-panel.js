export const meta = {
  name: 'irp-design-panel',
  description: 'IRP Audit mode (panel): generate N candidate approaches, adversarially verify/score each, synthesize the winner + grafts. args: { subject, problem, constraints, depth: Light|Standard|Deep, seeds?: [{key, angle}] }',
  phases: [{ title: 'Design+Verify' }, { title: 'Synthesize' }],
}

const A = args || {}
const subject = A.subject || 'the problem'
const PROBLEM = A.problem || subject
const CONSTRAINTS = A.constraints || 'Honor the stated hard constraints.'
const depth = A.depth || 'Standard'
const nSeeds = depth === 'Deep' ? 4 : depth === 'Light' ? 2 : 3
const seeds = (A.seeds && A.seeds.length)
  ? A.seeds
  : Array.from({ length: nSeeds }, (_, i) => ({ key: `opt-${i + 1}`, angle: `Design a distinct candidate approach (#${i + 1}) to: ${PROBLEM}` }))

const D = {
  type: 'object', required: ['approach', 'design', 'honest_strains'], additionalProperties: false,
  properties: { approach: { type: 'string' }, design: { type: 'string' }, honest_strains: { type: 'string' } },
}
const V = {
  type: 'object', required: ['approach', 'verdict', 'fatal_flaws', 'fixable_flaws', 'score'], additionalProperties: false,
  properties: {
    approach: { type: 'string' },
    verdict: { type: 'string', enum: ['strong', 'viable', 'weak', 'rejected'] },
    fatal_flaws: { type: 'array', items: { type: 'string' } },
    fixable_flaws: { type: 'array', items: { type: 'string' } },
    score: { type: 'number', description: '0-100' },
  },
}

phase('Design+Verify')
const results = await pipeline(
  seeds,
  s => agent(`${CONSTRAINTS}\n\nYou are an independent architect. Design THIS approach to the hilt (do not hedge toward the others):\n\nANGLE: ${s.angle}\n\nBe concrete and honest about where it strains. Return the structured object.`,
    { label: `design:${s.key}`, phase: 'Design+Verify', schema: D }),
  (d, s) => {
    if (!d) return null
    return agent(`${CONSTRAINTS}\n\nYou are an adversarial reviewer. Try to BREAK this design against the constraints; default to flagging when uncertain. Score it 0-100.\n\nDESIGN (${s.key}):\n${JSON.stringify(d, null, 2)}\n\nReturn the structured verdict.`,
      { label: `verify:${s.key}`, phase: 'Design+Verify', schema: V })
      .then(v => ({ seed: s.key, design: d, verdict: v }))
  }
)

phase('Synthesize')
const clean = results.filter(Boolean).filter(x => x && x.design)
const synth = await agent(
  `You are the lead architect for an IRP design panel. ${clean.length} candidate approaches, each adversarially scored, for:\n${PROBLEM}\n\nProduce markdown starting with an H1:\n# ${subject} — Design Panel\n## Recommendation (pick ONE primary design — do not present a menu)\n## Why (against the constraints + the scores)\n## Grafts (best ideas from the runners-up worth keeping)\n## What it gives up + operator decisions to surface\nReturn ONLY markdown from the H1.\n\nINPUTS:\n${JSON.stringify(clean, null, 2)}`,
  { label: 'synthesize', phase: 'Synthesize' })

return synth
