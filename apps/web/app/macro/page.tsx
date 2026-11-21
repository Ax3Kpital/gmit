import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { YieldCurvePanel } from '@/components/macro/YieldCurvePanel';
import { serverFetch } from '@/lib/server-api';

interface MacroSignals {
  yield_10y: number | null; yield_2y: number | null;
  spread_10y2y: number | null; yield_10y_delta30d: number | null;
  spread_delta30d: number | null; curve_shape: string;
  wti: number | null; wti_delta30d_pct: number | null;
  brent: number | null; oil_trend: string;
  sp500: number | null; sp500_delta30d_pct: number | null;
  nasdaq: number | null; nasdaq_delta30d_pct: number | null;
  equity_trend: string;
  eurusd: number | null; eurusd_delta30d_pct: number | null;
  usdjpy: number | null; usdjpy_delta30d_pct: number | null;
  usd_trend: string; macro_regime: string; as_of: string;
}

const REGIME_COLOR: Record<string, string> = {
  risk_on: '#3ecf8e', risk_off: '#f07178', stagflation: '#e6b84c',
  goldilocks: '#3ecf8e', tightening: '#e6b84c', easing: '#3d9cf0', mixed: '#8b98a8',
};
const REGIME_DESC: Record<string, string> = {
  risk_on: 'Equities advancing, risk assets bid, safe havens underperforming.',
  risk_off: 'Equities under pressure, safe havens bid, credit spreads widening.',
  stagflation: 'High inflation + slowing growth. Negative for bonds and equities.',
  goldilocks: 'Moderate growth + contained inflation. Positive for risk assets.',
  tightening: 'Rising rates environment. Pressure on duration and rate-sensitive sectors.',
  easing: 'Declining rates. Supportive for bonds, equities, and credit.',
  mixed: 'Conflicting signals. No dominant macro theme.',
};

function SignalRow({ label, value, delta, deltaUnit = '', trend, trendColor }:
  { label: string; value: string; delta?: string | null; deltaUnit?: string; trend?: string; trendColor?: string }) {
  return (
    <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--line)' }}>
      <span className="text-sm" style={{ color: 'var(--muted)' }}>{label}</span>
      <div className="text-right">
        <span className="mono font-medium" style={{ color: 'var(--text)' }}>{value}</span>
        {delta && (
          <span className="mono text-xs ml-2"
            style={{ color: delta.startsWith('+') ? 'var(--up)' : delta.startsWith('-') ? 'var(--down)' : 'var(--muted)' }}>
            {delta}{deltaUnit}/30d
          </span>
        )}
        {trend && (
          <span className="mono text-xs ml-2 uppercase" style={{ color: trendColor ?? 'var(--muted)' }}>
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}

function d(v: number | null, dec = 2) { return v !== null ? v.toFixed(dec) : 'N/A'; }
function dp(v: number | null) { return v !== null ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}` : null; }
function dpct(v: number | null) { return v !== null ? `${v >= 0 ? '+' : ''}${v.toFixed(1)}%` : null; }

export default async function MacroPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const s = await serverFetch<MacroSignals>('/api/macro/signals');

  const regimeColor = s ? (REGIME_COLOR[s.macro_regime] ?? '#8b98a8') : '#8b98a8';

  return (
    <AppShell title="Macro">
      <div className="p-5 space-y-5 max-w-5xl mx-auto">

        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          US macro signals — FRED data via Federal Reserve Bank of St. Louis. EOD, 1-2 day lag.
          {s?.as_of && <span className="ml-2">As of {s.as_of}.</span>}
        </p>

        {/* Regime badge */}
        {s && (
          <div className="rounded-xl p-4 flex items-start gap-4"
            style={{ background: 'var(--panel)', border: `1px solid ${regimeColor}33` }}>
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>
                Macro Regime
              </div>
              <span className="mono font-semibold text-lg" style={{ color: regimeColor }}>
                {s.macro_regime.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <p className="text-sm mt-0.5 leading-relaxed" style={{ color: 'var(--muted)' }}>
              {REGIME_DESC[s.macro_regime] ?? ''}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* Rates */}
          <Panel title="Rates & Yield Curve">
            <div className="px-4 pb-1">
              {s ? <>
                <SignalRow label="10Y Treasury Yield" value={`${d(s.yield_10y)}%`}
                  delta={dp(s.yield_10y_delta30d)} deltaUnit="pp" />
                <SignalRow label="2Y Treasury Yield" value={`${d(s.yield_2y)}%`} />
                <SignalRow label="10Y-2Y Spread" value={`${dp(s.spread_10y2y) ?? 'N/A'}%`}
                  delta={dp(s.spread_delta30d)} deltaUnit="pp"
                  trend={s.curve_shape} trendColor={s.curve_shape === 'inverted' ? 'var(--down)' : 'var(--up)'} />
              </> : <p className="py-6 text-xs text-center" style={{ color: 'var(--muted)' }}>Loading…</p>}
            </div>
          </Panel>

          {/* Commodities */}
          <Panel title="Commodities">
            <div className="px-4 pb-1">
              {s ? <>
                <SignalRow label="WTI Crude Oil" value={`$${d(s.wti)}`}
                  delta={dpct(s.wti_delta30d_pct)}
                  trend={s.oil_trend} trendColor={s.oil_trend === 'rising' ? 'var(--warn)' : 'var(--muted)'} />
                <SignalRow label="Brent Crude" value={`$${d(s.brent)}`} />
              </> : <p className="py-6 text-xs text-center" style={{ color: 'var(--muted)' }}>Loading…</p>}
            </div>
          </Panel>

          {/* Equities */}
          <Panel title="Equities">
            <div className="px-4 pb-1">
              {s ? <>
                <SignalRow label="S&P 500" value={s.sp500?.toLocaleString('en-US', { maximumFractionDigits: 0 }) ?? 'N/A'}
                  delta={dpct(s.sp500_delta30d_pct)}
                  trend={s.equity_trend} trendColor={s.equity_trend === 'bull' ? 'var(--up)' : s.equity_trend === 'bear' ? 'var(--down)' : 'var(--muted)'} />
                <SignalRow label="Nasdaq Composite" value={s.nasdaq?.toLocaleString('en-US', { maximumFractionDigits: 0 }) ?? 'N/A'}
                  delta={dpct(s.nasdaq_delta30d_pct)} />
              </> : <p className="py-6 text-xs text-center" style={{ color: 'var(--muted)' }}>Loading…</p>}
            </div>
          </Panel>

          {/* FX */}
          <Panel title="Foreign Exchange">
            <div className="px-4 pb-1">
              {s ? <>
                <SignalRow label="EUR/USD" value={d(s.eurusd, 4)}
                  delta={dpct(s.eurusd_delta30d_pct)}
                  trend={`USD ${s.usd_trend}`} />
                <SignalRow label="USD/JPY" value={d(s.usdjpy, 2)}
                  delta={dpct(s.usdjpy_delta30d_pct)} />
              </> : <p className="py-6 text-xs text-center" style={{ color: 'var(--muted)' }}>Loading…</p>}
            </div>
          </Panel>
        </div>

        {/* Yield curve chart */}
        <YieldCurvePanel />

        <p className="text-xs" style={{ color: 'var(--muted)', opacity: 0.5 }}>
          Source: FRED, Federal Reserve Bank of St. Louis — fred.stlouisfed.org. Not financial advice.
        </p>
      </div>
    </AppShell>
  );
}
