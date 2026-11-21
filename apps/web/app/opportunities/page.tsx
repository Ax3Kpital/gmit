import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { serverFetch } from '@/lib/server-api';

interface Thesis {
  id: string;
  topic: string;
  claim: string;
  confidence: number;
  time_horizon: string | null;
  provider: string;
  created_at: string;
}

interface MacroSignals {
  macro_regime: string;
  yield_10y: number | null;
  wti: number | null;
  sp500: number | null;
  sp500_delta30d_pct: number | null;
  equity_trend: string;
  oil_trend: string;
  curve_shape: string;
}

interface CotItem {
  cftc_code: string;
  display_name: string;
  percentile_52w: number | null;
  sentiment: string | null;
  net_noncomm: number | null;
}

interface CotResponse { items: CotItem[]; }

const CONF_COLOR = (c: number) => c >= 70 ? 'var(--up)' : c >= 50 ? 'var(--warn)' : 'var(--muted)';

function OppBadge({ label, color }: { label: string; color: string }) {
  return (
    <span className="text-xs mono px-2 py-0.5 rounded-full"
      style={{ color, border: `1px solid ${color}44` }}>
      {label}
    </span>
  );
}

export default async function OpportunitiesPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const [theses, signals, cotData] = await Promise.all([
    serverFetch<Thesis[]>('/api/research/theses') ?? [],
    serverFetch<MacroSignals>('/api/macro/signals'),
    serverFetch<CotResponse>('/api/smart-money/cot'),
  ]);

  const highConfidence = (theses ?? [])
    .filter(t => t.confidence >= 55 && t.provider !== 'mock')
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 6);

  const extremeCot = (cotData?.items ?? []).filter(
    i => i.percentile_52w !== null && (i.percentile_52w >= 80 || i.percentile_52w <= 20)
  );

  const regimeSignals: string[] = [];
  if (signals) {
    if (signals.macro_regime === 'easing') regimeSignals.push('Easing regime favors duration and credit');
    if (signals.macro_regime === 'risk_on') regimeSignals.push('Risk-on: equities and high-yield supported');
    if (signals.curve_shape === 'inverted') regimeSignals.push('Inverted curve: prepare for potential un-inversion trade');
    if (signals.equity_trend === 'bull') regimeSignals.push('Equity uptrend intact — momentum favorable');
    if (signals.oil_trend === 'rising') regimeSignals.push('Rising oil: energy sector and inflation hedges');
    if (signals.oil_trend === 'falling') regimeSignals.push('Falling oil: consumer discretionary and transport tailwind');
  }

  return (
    <AppShell title="Oportunități">
      <div className="p-5 space-y-5 max-w-5xl mx-auto">

        <div className="flex items-center justify-between">
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Opportunities derived from research theses, macro regime signals and COT extremes.
          </p>
          <Link href="/library"
            className="text-xs px-3 py-1.5 rounded-lg flex-shrink-0"
            style={{ background: 'var(--accent)', color: '#fff' }}>
            + Generate thesis
          </Link>
        </div>

        {/* Regime signals */}
        {regimeSignals.length > 0 && (
          <div className="rounded-xl p-4"
            style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            <h3 className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--muted)' }}>
              Regime Signals — {signals?.macro_regime?.replace('_', ' ').toUpperCase()}
            </h3>
            <div className="space-y-2">
              {regimeSignals.map((sig, i) => (
                <div key={i} className="flex items-start gap-2 text-sm" style={{ color: 'var(--text)' }}>
                  <span style={{ color: 'var(--accent)', flexShrink: 0 }}>›</span>
                  <span>{sig}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* COT contrarian signals */}
        {extremeCot.length > 0 && (
          <div>
            <h3 className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--muted)' }}>
              COT Extreme Positioning — Contrarian Signals
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {extremeCot.map(item => {
                const isLong = (item.percentile_52w ?? 50) >= 80;
                return (
                  <div key={item.cftc_code} className="rounded-xl p-4"
                    style={{ background: 'var(--panel)', border: `1px solid ${isLong ? '#e6b84c33' : '#f0717833'}` }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{item.display_name}</span>
                      <OppBadge
                        label={isLong ? 'EXTREME LONG' : 'EXTREME SHORT'}
                        color={isLong ? 'var(--warn)' : 'var(--down)'}
                      />
                    </div>
                    <div className="text-xs" style={{ color: 'var(--muted)' }}>
                      {item.percentile_52w?.toFixed(0)}th percentile (52-week)
                    </div>
                    <div className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                      {isLong
                        ? 'Specs heavily long — potential crowded trade, watch for unwind'
                        : 'Specs heavily short — potential squeeze risk, watch for reversal'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* High-confidence theses */}
        <div>
          <h3 className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--muted)' }}>
            High-Confidence Research Theses
          </h3>
          {highConfidence.length === 0 ? (
            <div className="rounded-xl p-10 text-center"
              style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                No high-confidence theses yet.{' '}
                <Link href="/library" style={{ color: 'var(--accent)' }}>Generate one</Link>
                {' '}to see opportunities here.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {highConfidence.map(t => (
                <div key={t.id} className="rounded-xl p-4"
                  style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{t.topic}</span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="mono font-bold text-sm" style={{ color: CONF_COLOR(t.confidence) }}>
                        {t.confidence}%
                      </span>
                      {t.time_horizon && (
                        <OppBadge label={t.time_horizon} color="var(--muted)" />
                      )}
                    </div>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>{t.claim}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-xs" style={{ color: 'var(--muted)' }}>
                      {new Date(t.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                    <Link href="/library" className="text-xs" style={{ color: 'var(--accent)' }}>
                      View full thesis →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </AppShell>
  );
}
