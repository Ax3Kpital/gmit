import { getTranslations } from 'next-intl/server';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { AutoRefresh } from '@/components/ui/AutoRefresh';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { StatusTile } from '@/components/ui/StatusTile';
import { DataStatusBadge } from '@/components/ui/Badge';
import { YieldCurvePanel } from '@/components/macro/YieldCurvePanel';
import { serverFetch } from '@/lib/server-api';
import { isFresh } from '@/lib/freshness';

interface MacroSignals {
  yield_10y: number | null;
  yield_2y: number | null;
  spread_10y2y: number | null;
  yield_10y_delta30d: number | null;
  spread_delta30d: number | null;
  curve_shape: string;
  wti: number | null;
  wti_delta30d_pct: number | null;
  brent: number | null;
  oil_trend: string;
  sp500: number | null;
  sp500_delta30d_pct: number | null;
  nasdaq: number | null;
  nasdaq_delta30d_pct: number | null;
  equity_trend: string;
  eurusd: number | null;
  eurusd_delta30d_pct: number | null;
  usdjpy: number | null;
  usdjpy_delta30d_pct: number | null;
  usd_trend: string;
  macro_regime: string;
  as_of: string;
}

interface Briefing {
  id: string;
  date: string;
  macro_regime: string | null;
  headline: string | null;
  key_moves: string[];
  cot_highlights: string[];
  watchlist: string[];
  generated_at: string | null;
}

const REGIME_COLOR: Record<string, string> = {
  risk_on:     '#3ecf8e',
  risk_off:    '#f07178',
  stagflation: '#e6b84c',
  goldilocks:  '#3ecf8e',
  tightening:  '#e6b84c',
  easing:      '#3d9cf0',
  mixed:       '#8b98a8',
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

function delta(v: number | null, unit = '', decimals = 1) {
  if (v === null) return null;
  const sign = v >= 0 ? '+' : '';
  return `${sign}${v.toFixed(decimals)}${unit}`;
}

interface ThesisWithScenarios {
  id: string;
  topic: string;
  confidence: number;
  created_at: string;
  scenarios: { id: string; name: string; probability: number }[];
}

interface CotExtreme {
  display_name: string;
  sentiment: string | null;
  percentile_52w: number | null;
}

export default async function DashboardPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const t = await getTranslations();

  const [signals, briefing, theses, cot] = await Promise.all([
    serverFetch<MacroSignals>('/api/macro/signals'),
    serverFetch<Briefing>('/api/briefings/latest'),
    serverFetch<ThesisWithScenarios[]>('/api/research/theses/with-scenarios'),
    serverFetch<{ items: CotExtreme[] }>('/api/smart-money/cot'),
  ]);
  const latestThesis = (theses ?? []).find(th => th.scenarios.length > 0 && isFresh(th.created_at)) ?? null;
  const extremes = (cot?.items ?? []).filter(i => (i.sentiment ?? '').startsWith('extreme')).slice(0, 4);

  const regimeColor = signals ? REGIME_COLOR[signals.macro_regime] ?? '#8b98a8' : '#8b98a8';
  const regimeLabel = signals ? REGIME_LABEL[signals.macro_regime] ?? signals.macro_regime.toUpperCase() : '—';

  const MARKET_TAPE = signals ? [
    { label: 'S&P 500',    value: signals.sp500 ? signals.sp500.toLocaleString('en-US', { maximumFractionDigits: 0 }) : '—', delta: delta(signals.sp500_delta30d_pct, '%') },
    { label: 'Nasdaq',     value: signals.nasdaq ? signals.nasdaq.toLocaleString('en-US', { maximumFractionDigits: 0 }) : '—', delta: delta(signals.nasdaq_delta30d_pct, '%') },
    { label: 'WTI Crude',  value: signals.wti ? `$${signals.wti.toFixed(2)}` : '—', delta: delta(signals.wti_delta30d_pct, '%') },
    { label: 'Brent',      value: signals.brent ? `$${signals.brent.toFixed(2)}` : '—', delta: null },
    { label: '10Y UST',    value: signals.yield_10y ? `${signals.yield_10y.toFixed(2)}%` : '—', delta: delta(signals.yield_10y_delta30d, 'pp') },
    { label: 'EUR/USD',    value: signals.eurusd ? signals.eurusd.toFixed(4) : '—', delta: delta(signals.eurusd_delta30d_pct, '%') },
    { label: 'USD/JPY',    value: signals.usdjpy ? signals.usdjpy.toFixed(2) : '—', delta: delta(signals.usdjpy_delta30d_pct, '%') },
  ] : [];

  const REGIME_TILES = [
    { label: 'Regime',        value: regimeLabel,                        color: regimeColor },
    { label: 'Yield Curve',   value: signals?.curve_shape?.toUpperCase() ?? '—', color: signals?.curve_shape === 'inverted' ? '#f07178' : '#3ecf8e' },
    { label: 'Equities',      value: signals?.equity_trend?.toUpperCase() ?? '—', color: signals?.equity_trend === 'bull' ? '#3ecf8e' : signals?.equity_trend === 'bear' ? '#f07178' : '#8b98a8' },
    { label: 'Oil',           value: signals?.oil_trend?.toUpperCase() ?? '—', color: signals?.oil_trend === 'rising' ? '#e6b84c' : '#8b98a8' },
    { label: 'USD',           value: signals?.usd_trend?.toUpperCase() ?? '—', color: '#8b98a8' },
    { label: 'Data as of',    value: signals?.as_of ?? '—', color: '#8b98a8' },
  ];

  return (
    <AppShell title={t('commandCenter.title')}>
      <AutoRefresh seconds={60} />
      <div className="p-5 space-y-5">

        {/* Market tape */}
        <div
          className="flex items-center gap-0 overflow-x-auto rounded-xl"
          style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
        >
          <span className="px-3 py-2.5 text-xs uppercase tracking-widest flex-shrink-0"
            style={{ color: 'var(--muted)', borderRight: '1px solid var(--line)' }}>
            {t('commandCenter.marketTape')}
          </span>
          {signals ? MARKET_TAPE.map(({ label, value, delta: d }) => (
            <div key={label} className="flex flex-col px-4 py-2 flex-shrink-0"
              style={{ borderRight: '1px solid var(--line)' }}>
              <span className="text-xs" style={{ color: 'var(--muted)' }}>{label}</span>
              <span className="mono text-sm font-medium mt-0.5" style={{ color: 'var(--text)' }}>{value}</span>
              {d && (
                <span className="mono text-xs" style={{
                  color: d.startsWith('+') ? 'var(--up)' : d.startsWith('-') ? 'var(--down)' : 'var(--muted)',
                }}>{d}/30d</span>
              )}
            </div>
          )) : (
            <div className="px-4 py-3">
              <span className="text-xs" style={{ color: 'var(--muted)' }}>Loading market data…</span>
            </div>
          )}
          <div className="px-3 py-2 ml-auto flex-shrink-0">
            <DataStatusBadge status={signals ? 'END_OF_DAY' : 'UNAVAILABLE'} />
          </div>
        </div>

        {/* Yield curve */}
        <YieldCurvePanel />

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Regime panel */}
          <div className="lg:col-span-2">
            <Panel title={t('commandCenter.marketRegime')}>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4">
                {REGIME_TILES.map(({ label, value, color }) => (
                  <div key={label} className="rounded-xl p-3"
                    style={{ background: 'var(--bg)', border: '1px solid var(--line)' }}>
                    <div className="text-xs mb-1" style={{ color: 'var(--muted)' }}>{label}</div>
                    <div className="mono font-semibold text-sm" style={{ color }}>{value}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          {/* Briefing summary */}
          <div>
            <Panel title="Daily Briefing">
              {briefing ? (
                <div className="p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs mono px-2 py-0.5 rounded-full"
                      style={{
                        color: regimeColor,
                        border: `1px solid ${regimeColor}`,
                      }}>
                      {regimeLabel}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--muted)' }}>
                      {briefing.date}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
                    {briefing.headline}
                  </p>
                  {briefing.key_moves.slice(0, 3).map((m, i) => (
                    <div key={i} className="flex gap-2 text-xs" style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--line)' }}>›</span>
                      <span>{m}</span>
                    </div>
                  ))}
                  <Link href="/briefings"
                    className="text-xs block mt-2"
                    style={{ color: 'var(--accent)' }}>
                    Full briefing →
                  </Link>
                </div>
              ) : (
                <div className="p-4 flex flex-col items-center justify-center min-h-40">
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>
                    Generating first briefing…
                  </span>
                </div>
              )}
            </Panel>
          </div>
        </div>

        {/* Active scenarios + opportunities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Panel title={t('commandCenter.activeScenarios')}>
            {latestThesis ? (
              <div className="p-4 space-y-2">
                <div className="text-xs" style={{ color: 'var(--muted)' }}>
                  {latestThesis.topic} · confidence {latestThesis.confidence}%
                </div>
                {latestThesis.scenarios.slice(0, 3).map(sc => (
                  <div key={sc.id} className="flex items-center justify-between text-sm">
                    <span style={{ color: 'var(--text)' }}>{sc.name}</span>
                    <span className="mono text-xs" style={{ color: 'var(--accent)' }}>{sc.probability}%</span>
                  </div>
                ))}
                <Link href="/scenarios" className="text-xs" style={{ color: 'var(--accent)' }}>All scenarios →</Link>
              </div>
            ) : (
              <div className="p-4 flex items-center justify-center min-h-32">
                <span className="text-xs" style={{ color: 'var(--muted)' }}>No recent theses — generate a fresh one in the Research Library</span>
              </div>
            )}
          </Panel>
          <Panel title={t('commandCenter.topOpportunities')}>
            {extremes.length > 0 ? (
              <div className="p-4 space-y-2">
                {extremes.map(e => (
                  <div key={e.display_name} className="flex items-center justify-between text-sm">
                    <span style={{ color: 'var(--text)' }}>{e.display_name}</span>
                    <span className="mono text-xs" style={{ color: 'var(--down)' }}>
                      {(e.sentiment ?? '').replace('_', ' ').toUpperCase()}
                      {e.percentile_52w !== null ? ` · ${Math.round(e.percentile_52w)}th pct` : ''}
                    </span>
                  </div>
                ))}
                <Link href="/opportunities" className="text-xs" style={{ color: 'var(--accent)' }}>All opportunities →</Link>
              </div>
            ) : (
              <div className="p-4 flex items-center justify-center min-h-32">
                <span className="text-xs" style={{ color: 'var(--muted)' }}>No extreme positioning right now</span>
              </div>
            )}
          </Panel>
        </div>

      </div>
    </AppShell>
  );
}
