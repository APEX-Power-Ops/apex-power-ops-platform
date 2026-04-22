import React, { useState } from 'react';

const BlueSkyArchitecture = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedIntegration, setExpandedIntegration] = useState(null);

  const integrations = [
    {
      id: 'powersync',
      name: 'PowerSync',
      category: 'Offline-First',
      stars: 5,
      impact: 'CRITICAL',
      problem: 'Field techs need offline access',
      solution: 'Drop-in sync layer, SQLite on device',
      effort: '8-16 hours',
      customAlternative: '100+ hours',
      cost: 'Free tier → $50-100/mo',
      color: 'emerald'
    },
    {
      id: 'reactadmin',
      name: 'React-admin + ra-supabase',
      category: 'Admin UI',
      stars: 5,
      impact: 'HIGH',
      problem: 'Need PM dashboard fast',
      solution: 'Auto-generate CRUD from tables',
      effort: '8-16 hours',
      customAlternative: '80+ hours',
      cost: 'Free (open source)',
      color: 'blue'
    },
    {
      id: 'algolia',
      name: 'Algolia',
      category: 'Search',
      stars: 4,
      impact: 'MEDIUM',
      problem: 'SharePoint-style search needed',
      solution: 'Instant, typo-tolerant search',
      effort: '4-8 hours',
      customAlternative: 'Postgres OK for MVP',
      cost: 'Free tier → $50/mo',
      color: 'purple'
    },
    {
      id: 'onesignal',
      name: 'OneSignal',
      category: 'Notifications',
      stars: 4,
      impact: 'MEDIUM',
      problem: 'Field techs need alerts',
      solution: 'Push, email, SMS unified',
      effort: '4-8 hours',
      customAlternative: '40+ hours',
      cost: 'Free tier generous',
      color: 'orange'
    },
    {
      id: 'triggerdev',
      name: 'Trigger.dev',
      category: 'Background Jobs',
      stars: 3,
      impact: 'MEDIUM',
      problem: 'PowerDB sync, reports',
      solution: 'Serverless jobs, no timeouts',
      effort: '4-8 hours',
      customAlternative: '20+ hours',
      cost: 'Free tier',
      color: 'cyan'
    },
    {
      id: 'resend',
      name: 'Resend',
      category: 'Email',
      stars: 3,
      impact: 'LOW',
      problem: 'Transactional emails',
      solution: 'Modern, developer-focused',
      effort: '2-4 hours',
      customAlternative: '8+ hours',
      cost: '3K free/mo',
      color: 'pink'
    }
  ];

  const phases = [
    { phase: 1, name: 'Foundation', weeks: '1-2', items: ['Supabase Auth', 'React-admin setup', 'Basic PM dashboard', 'Document storage'] },
    { phase: 2, name: 'Document Hub', weeks: '3-4', items: ['Upload UI', 'Folder structure', 'Search', 'Link to apparatus'] },
    { phase: 3, name: 'PowerSync', weeks: '5-6', items: ['PowerSync service', 'Sync rules', 'RN app shell', 'SDK integration'] },
    { phase: 4, name: 'Field Tech MVP', weeks: '7-10', items: ['My Assignments', 'Apparatus detail', 'Mark complete', 'Time entry', 'Offline docs'] },
    { phase: 5, name: 'Polish', weeks: '11-14', items: ['PowerDB sync', 'Push notifications', 'Reports', 'Study content'] },
    { phase: 6, name: 'Advanced', weeks: '15+', items: ['Algolia upgrade', 'Client portal', 'Analytics', 'TCC integration'] }
  ];

  const getColorClasses = (color) => {
    const colors = {
      emerald: 'bg-emerald-500 border-emerald-600',
      blue: 'bg-blue-500 border-blue-600',
      purple: 'bg-purple-500 border-purple-600',
      orange: 'bg-orange-500 border-orange-600',
      cyan: 'bg-cyan-500 border-cyan-600',
      pink: 'bg-pink-500 border-pink-600'
    };
    return colors[color] || 'bg-gray-500 border-gray-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6 text-white">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            🚀 RESA Blue-Sky Architecture
          </h1>
          <p className="text-slate-300 text-lg">The Ideal Build With No Limitations</p>
          <div className="mt-4 inline-block bg-emerald-500/20 border border-emerald-500 rounded-lg px-4 py-2">
            <span className="text-emerald-400 font-semibold">10-14 weeks to production</span>
            <span className="text-slate-400 mx-2">vs</span>
            <span className="text-red-400">6-12 months building custom</span>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="flex justify-center gap-2 mb-6">
          {['overview', 'integrations', 'timeline', 'costs'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === tab 
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30' 
                  : 'bg-white/10 hover:bg-white/20 text-slate-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Architecture Diagram */}
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <h2 className="text-xl font-bold mb-4 text-center">Three Frontends, One Backend</h2>
              
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-orange-500/20 border border-orange-500 rounded-xl p-4 text-center">
                  <div className="text-3xl mb-2">📱</div>
                  <div className="font-bold text-orange-400">Field Tech App</div>
                  <div className="text-sm text-slate-300">React Native + PowerSync</div>
                  <div className="mt-2 bg-orange-500 text-white text-xs px-2 py-1 rounded-full inline-block">
                    OFFLINE-FIRST
                  </div>
                </div>
                <div className="bg-blue-500/20 border border-blue-500 rounded-xl p-4 text-center">
                  <div className="text-3xl mb-2">🖥️</div>
                  <div className="font-bold text-blue-400">PM Dashboard</div>
                  <div className="text-sm text-slate-300">Next.js + shadcn</div>
                  <div className="mt-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full inline-block">
                    CUSTOM UX
                  </div>
                </div>
                <div className="bg-purple-500/20 border border-purple-500 rounded-xl p-4 text-center">
                  <div className="text-3xl mb-2">⚙️</div>
                  <div className="font-bold text-purple-400">Admin Panel</div>
                  <div className="text-sm text-slate-300">React-admin</div>
                  <div className="mt-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full inline-block">
                    AUTO-GENERATED
                  </div>
                </div>
              </div>

              <div className="flex justify-center mb-4">
                <div className="text-4xl">⬇️</div>
              </div>

              <div className="bg-emerald-500/20 border border-emerald-500 rounded-xl p-4 text-center max-w-md mx-auto">
                <div className="text-3xl mb-2">🗄️</div>
                <div className="font-bold text-emerald-400">Supabase</div>
                <div className="flex justify-center gap-2 mt-2 flex-wrap">
                  {['Postgres', 'Auth', 'Storage', 'Realtime'].map(svc => (
                    <span key={svc} className="bg-emerald-500/30 text-emerald-300 text-xs px-2 py-1 rounded-full">
                      {svc}
                    </span>
                  ))}
                </div>
                <div className="text-sm text-slate-300 mt-2">40 tables • Enterprise-grade • Already built ✅</div>
              </div>
            </div>

            {/* Key Insight */}
            <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500 rounded-xl p-6">
              <h3 className="text-xl font-bold text-yellow-400 mb-3">💡 Key Insight</h3>
              <p className="text-slate-200 leading-relaxed">
                <strong>PowerSync</strong> solves the hardest problem (offline sync) completely. 
                <strong> React-admin</strong> solves the second hardest problem (admin UI) almost completely. 
                Everything else is integration work, not invention.
              </p>
            </div>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="space-y-4">
            {integrations.map(int => (
              <div 
                key={int.id}
                className={`bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-all ${
                  expandedIntegration === int.id ? 'ring-2 ring-purple-500' : ''
                }`}
              >
                <div 
                  className="p-4 cursor-pointer hover:bg-white/5"
                  onClick={() => setExpandedIntegration(expandedIntegration === int.id ? null : int.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-12 rounded-full ${getColorClasses(int.color)}`}></div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-lg">{int.name}</span>
                          <span className="text-yellow-400">{'⭐'.repeat(int.stars)}</span>
                        </div>
                        <span className="text-sm text-slate-400">{int.category}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        int.impact === 'CRITICAL' ? 'bg-red-500 text-white' :
                        int.impact === 'HIGH' ? 'bg-orange-500 text-white' :
                        'bg-blue-500 text-white'
                      }`}>
                        {int.impact}
                      </span>
                      <span className="text-2xl">{expandedIntegration === int.id ? '▲' : '▼'}</span>
                    </div>
                  </div>
                </div>
                
                {expandedIntegration === int.id && (
                  <div className="border-t border-white/10 p-4 bg-black/20">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Problem</div>
                        <div className="text-white">{int.problem}</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Solution</div>
                        <div className="text-white">{int.solution}</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Integration Effort</div>
                        <div className="text-emerald-400 font-bold">{int.effort}</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Custom Alternative</div>
                        <div className="text-red-400 font-bold">{int.customAlternative}</div>
                      </div>
                      <div className="col-span-2">
                        <div className="text-sm text-slate-400 mb-1">Cost</div>
                        <div className="text-white">{int.cost}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="space-y-4">
            {phases.map((phase, idx) => (
              <div key={phase.phase} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                    phase.phase <= 2 ? 'bg-emerald-500' :
                    phase.phase <= 4 ? 'bg-blue-500' :
                    'bg-purple-500'
                  }`}>
                    {phase.phase}
                  </div>
                  {idx < phases.length - 1 && (
                    <div className="w-0.5 h-full bg-white/20 my-2"></div>
                  )}
                </div>
                <div className="flex-1 bg-white/5 border border-white/10 rounded-xl p-4 mb-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-bold text-lg">{phase.name}</h3>
                      <span className="text-sm text-slate-400">Weeks {phase.weeks}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      phase.phase <= 2 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500' :
                      phase.phase <= 4 ? 'bg-blue-500/20 text-blue-400 border border-blue-500' :
                      'bg-purple-500/20 text-purple-400 border border-purple-500'
                    }`}>
                      {phase.phase <= 2 ? 'Foundation' : phase.phase <= 4 ? 'MVP' : 'Enhancement'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {phase.items.map((item, i) => (
                      <span key={i} className="bg-white/10 text-slate-300 text-sm px-3 py-1 rounded-full">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Costs Tab */}
        {activeTab === 'costs' && (
          <div className="space-y-6">
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">Monthly Production Costs</h3>
              <div className="space-y-3">
                {[
                  { service: 'Supabase Pro', free: '$25/mo', prod: '$25-50/mo' },
                  { service: 'PowerSync', free: 'Free (dev)', prod: '$50-100/mo' },
                  { service: 'Algolia', free: '10K free', prod: '$0-50/mo' },
                  { service: 'OneSignal', free: 'Free tier', prod: '$0-25/mo' },
                  { service: 'Trigger.dev', free: 'Free tier', prod: '$0-25/mo' },
                  { service: 'Resend', free: '3K free', prod: '$0-20/mo' },
                  { service: 'Vercel', free: 'Free tier', prod: '$0-20/mo' }
                ].map(item => (
                  <div key={item.service} className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-slate-300">{item.service}</span>
                    <div className="flex gap-6">
                      <span className="text-emerald-400 w-24 text-right">{item.free}</span>
                      <span className="text-white w-24 text-right">{item.prod}</span>
                    </div>
                  </div>
                ))}
                <div className="flex justify-between items-center pt-4 font-bold text-lg">
                  <span>Total</span>
                  <span className="text-emerald-400">$75-290/month</span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500 rounded-xl p-6">
              <h3 className="text-xl font-bold text-red-400 mb-3">💸 Opportunity Cost Comparison</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="text-slate-400 mb-2">Building Custom</div>
                  <div className="text-3xl font-bold text-red-400">200+ hours</div>
                  <div className="text-slate-400">@ $100/hr = $20,000+</div>
                </div>
                <div>
                  <div className="text-slate-400 mb-2">Using Integrations</div>
                  <div className="text-3xl font-bold text-emerald-400">40-60 hours</div>
                  <div className="text-slate-400">+ $290/mo services</div>
                </div>
              </div>
              <div className="mt-4 text-center text-white">
                <strong>Break-even in ~1 month</strong> • Services pay for themselves immediately
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-8 text-center text-slate-500 text-sm">
          <p>Blue-Sky Architecture Analysis • December 26, 2025</p>
          <p className="mt-1">RESA Power Platform</p>
        </footer>
      </div>
    </div>
  );
};

export default BlueSkyArchitecture;
