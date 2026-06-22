export const meta = {
  name: 'irp-viewpoint-fanout',
  description: 'IRP Viewpoint mode: N independent, non-leading, blind-to-each-other design viewpoints on a problem -> synthesis (convergence vs genuine forks). args: { subject, problem, guardrails, depth: Light|Standard|Deep, n?, lenses?: string[] }',
  phases: [{ title: 'Viewpoints' }, { title: 'Synthesize' }],
}

const A = args || {}
const subject = A.subject || 'the problem'
const PROBLEM = A.problem || subject
const GUARD = A.guardrails || 'Honor the stated hard constraints; otherwise design freely.'
const depth = A.depth || 'Standard'
const N = A.n || (depth === 'Deep' ? 6 : depth === 'Light' ? 2 : 4)
const lenses = A.lenses || []

const VIEW_SCHEMA = {
  type: 'object',
  required: ['approach', 'design', 'strengths', 'risks'],
  additionalProperties: false,
  properties: {
    approach: { type: 'string' },
    design: { type: 'string', description: 'the core design in concrete terms' },
    strengths: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
  },
}

phase('Viewpoints')
const views = (await parallel(Array.from({ length: N }, (_, i) => () => {
  const lens = lenses[i]
    ? `Start from this angle and develop it fully (do not hedge toward the others): ${lenses[i]}.`
    : 'Develop your own strongest independent design.'
  return agent(
    `You are ONE of several INDEPENDENT reviewers, each working BLIND to the others — do not assume any shared answer. Produce an independent viewpoint/design for:\n\nPROBLEM: ${PROBLEM}\n\nHARD GUARDRAILS (do not violate): ${GUARD}\n\n${lens}\n\nBe concrete. Surface where your design is strong and where it is weak. Return the structured object.`,
    { label: `view-${i + 1}`, phase: 'Viewpoints', schema: VIEW_SCHEMA })
})).filter(Boolean)

phase('Synthesize')
const synth = await agent(
  `You are the synthesizer for an IRP Viewpoint review. Below are ${views.length} INDEPENDENT design viewpoints on:\n${PROBLEM}\n\nProduce a markdown synthesis starting with an H1, with exactly these sections:\n# ${subject} — Viewpoint Synthesis\n## Convergence (what all/most landed on — bankable)\n## Genuine forks (where they truly diverge, with the trade-off)\n## Distinct ideas worth keeping regardless of direction\n## Guardrail check (any viewpoint that strains the hard guardrails)\n## Recommended direction + operator decisions to surface (with leans)\nBe decisive. Return ONLY markdown from the H1.\n\nVIEWPOINTS:\n${JSON.stringify(views, null, 2)}`,
  { label: 'synthesize', phase: 'Synthesize' })

return synth
