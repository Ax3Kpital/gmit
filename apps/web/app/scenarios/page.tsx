import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { serverFetch } from '@/lib/server-api';

interface Scenario {
  id: string;
  name: string;
  probability: number | null;
  description: string | null;
  trigger: string | null;
  thesis_id: string;
  thesis_topic: string;
}

interface ThesisWithScenarios {
  id: string;
  topic: string;
  claim: string;
  confidence: number;
  macro_regime: string | null;
  created_at: string;
  scenarios: Scenario[];
}

const PROB_COLOR = (p: number | null) => {
  if (p === null) return 'var(--muted)';
  if (p >= 60) return 'var(--up)';
  if (p >= 35) return 'var(--warn)';
  return 'var(--muted)';
};

export default async function ScenariosPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const theses = await serverFetch<ThesisWithScenarios[]>('/api/research/theses/with-scenarios') ?? [];

  const allScenarios = theses.flatMap(t =>
    (t.scenarios ?? []).map(s => ({ ...s, thesis_topic: t.topic, thesis_id: t.id }))
  );

  const hasData = allScenarios.length > 0;

  return (
    <AppShell title="Scenarios">
      <div className="p-5 space-y-5 max-w-5xl mx-auto">

        <div className="flex items-center justify-between">
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Investment scenarios derived from research theses — probability-weighted outcomes per thesis.
          </p>
          <Link href="/library"
            className="text-xs px-3 py-1.5 rounded-lg flex-shrink-0"
            style={{ background: 'var(--accent)', color: '#fff' }}>
            + New thesis
          </Link>
        </div>

        {!hasData ? (
          <div className="rounded-xl p-10 text-center space-y-3"
            style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>No scenarios yet</p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              Scenarios are automatically extracted from research theses.
              Generate a thesis in the{' '}
              <Link href="/library" style={{ color: 'var(--accent)' }}>Research Library</Link>
              {' '}to see scenarios here.
            </p>
          </div>
        ) : (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Total scenarios', value: allScenarios.length },
                { label: 'From theses', value: theses.filter(t => t.scenarios?.length > 0).length },
                { label: 'High probability (≥60%)', value: allScenarios.filter(s => (s.probability ?? 0) >= 60).length },
              ].map(stat => (
                <div key={stat.label} className="rounded-xl p-4"
                  style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
                  <div className="text-xs mb-1" style={{ color: 'var(--muted)' }}>{stat.label}</div>
                  <div className="mono text-xl font-semibold" style={{ color: 'var(--text)' }}>{stat.value}</div>
                </div>
              ))}
            </div>

            {/* Scenarios grouped by thesis */}
            {theses.filter(t => t.scenarios?.length > 0).map(thesis => (
              <div key={thesis.id} className="rounded-xl overflow-hidden"
                style={{ border: '1px solid var(--line)' }}>
                <div className="px-5 py-3 flex items-center justify-between"
                  style={{ background: 'var(--panel)', borderBottom: '1px solid var(--line)' }}>
                  <div>
                    <Link href="/library" className="text-sm font-medium hover:underline"
                      style={{ color: 'var(--text)' }}>
                      {thesis.topic}
                    </Link>
                    <span className="ml-2 text-xs mono" style={{ color: 'var(--muted)' }}>
                      {thesis.confidence}% confidence
                    </span>
                  </div>
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>
                    {new Date(thesis.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
                <div>
                  {thesis.scenarios.map((s, i) => (
                    <div key={s.id}
                      className="px-5 py-4 flex items-start gap-4"
                      style={{
                        borderBottom: i < thesis.scenarios.length - 1 ? '1px solid var(--line)' : 'none',
                        background: i % 2 === 0 ? 'var(--bg)' : 'var(--panel)',
                      }}>
                      <div className="flex-shrink-0 text-center" style={{ minWidth: '48px' }}>
                        <div className="mono font-bold text-base" style={{ color: PROB_COLOR(s.probability) }}>
                          {s.probability !== null ? `${s.probability}%` : '—'}
                        </div>
                        <div className="text-xs" style={{ color: 'var(--muted)' }}>prob</div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>{s.name}</div>
                        {s.description && (
                          <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>{s.description}</p>
                        )}
                        {s.trigger && (
                          <div className="mt-1.5 flex items-start gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
                            <span style={{ color: 'var(--warn)' }}>⚡ Trigger:</span>
                            <span>{s.trigger}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </AppShell>
  );
}
