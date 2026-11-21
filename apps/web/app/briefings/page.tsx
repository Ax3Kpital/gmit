import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { serverFetch } from '@/lib/server-api';

interface Briefing {
  id: string;
  date: string;
  macro_regime: string | null;
  headline: string | null;
  key_moves: string[];
  cot_highlights: string[];
  alert_summary: string[];
  watchlist: string[];
  generated_at: string | null;
}

const REGIME_COLOR: Record<string, string> = {
  risk_on:     'var(--up)',
  risk_off:    'var(--down)',
  stagflation: 'var(--warn)',
  goldilocks:  'var(--up)',
  tightening:  'var(--warn)',
  easing:      'var(--accent)',
  mixed:       'var(--muted)',
};

const REGIME_LABEL: Record<string, string> = {
  risk_on:     'RISK ON',
  risk_off:    'RISK OFF',
  stagflation: 'STAGFLATION',
  goldilocks:  'GOLDILOCKS',
  tightening:  'TIGHTENING',
  easing:      'EASING',
  mixed:       'MIXED',
};

function BriefingCard({ b, expanded }: { b: Briefing; expanded: boolean }) {
  const color = REGIME_COLOR[b.macro_regime ?? 'mixed'] ?? 'var(--muted)';

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>

      {/* Header */}
      <div className="px-5 py-4 flex items-start justify-between gap-4"
        style={{ borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="mono font-semibold" style={{ color: 'var(--text)' }}>
              {new Date(b.date + 'T00:00:00').toLocaleDateString('en-US', {
                weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
              })}
            </span>
            <span className="text-xs mono px-2 py-0.5 rounded-full"
              style={{ color, border: `1px solid ${color}` }}>
              {REGIME_LABEL[b.macro_regime ?? 'mixed'] ?? b.macro_regime}
            </span>
          </div>
          {b.headline && (
            <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
              {b.headline}
            </p>
          )}
        </div>
      </div>

      {expanded && (
        <div className="p-5 space-y-5">
          {b.key_moves.length > 0 && (
            <Section title="Key Moves" items={b.key_moves} color="var(--accent)" />
          )}
          {b.cot_highlights.length > 0 && (
            <Section title="COT Highlights" items={b.cot_highlights} color="var(--warn)" />
          )}
          {b.alert_summary.length > 0 && (
            <Section title="Alerts" items={b.alert_summary} color="var(--down)" />
          )}
          {b.watchlist.length > 0 && (
            <Section title="Watchlist" items={b.watchlist} color="var(--muted)" />
          )}
        </div>
      )}
    </div>
  );
}

function Section({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <h4 className="text-xs uppercase tracking-wider mb-2 font-medium" style={{ color }}>
        {title}
      </h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text)' }}>
            <span style={{ color: 'var(--line)', flexShrink: 0 }}>›</span>
            <span className="leading-relaxed">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default async function BriefingsPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const briefings = await serverFetch<Briefing[]>('/api/briefings?limit=30') ?? [];

  return (
    <AppShell title="Daily Briefing">
      <div className="p-5 space-y-4 max-w-4xl mx-auto">

        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Rule-based daily macro briefing — regime classification, COT signals, watchlist. Generated at 07:00 UTC.
        </p>

        {briefings.length === 0 ? (
          <div className="rounded-xl p-10 text-center"
            style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              No briefings yet. First briefing generates automatically at 07:00 UTC.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {briefings.map((b, i) => (
              <BriefingCard key={b.id} b={b} expanded={i === 0} />
            ))}
          </div>
        )}

      </div>
    </AppShell>
  );
}
