'use client';

export interface CotItem {
  cftc_code: string;
  display_name: string;
  category: string;
  exchange: string | null;
  related_series_id: string | null;
  data_status: string;
  latest_report_date: string | null;
  net_noncomm: number | null;
  net_noncomm_pct_oi: number | null;
  percentile_52w: number | null;
  sentiment: string | null;
  change_net_wow: number | null;
  open_interest: number | null;
  history: { date: string; net_noncomm: number | null; open_interest: number | null }[];
}

const SENTIMENT_COLOR: Record<string, string> = {
  extreme_long:  'var(--warn)',
  long:          'var(--up)',
  neutral:       'var(--muted)',
  short:         'var(--down)',
  extreme_short: 'var(--down)',
};

const SENTIMENT_LABEL: Record<string, string> = {
  extreme_long:  'EXTREME LONG',
  long:          'LONG',
  neutral:       'NEUTRAL',
  short:         'SHORT',
  extreme_short: 'EXTREME SHORT',
};

function fmt(n: number | null, decimals = 0): string {
  if (n === null) return 'N/A';
  if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { maximumFractionDigits: decimals });
  return n.toFixed(decimals);
}

function PercentileBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 80 ? 'var(--warn)' : pct <= 20 ? 'var(--down)' : pct >= 60 ? 'var(--up)' : 'var(--muted)';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs" style={{ color: 'var(--muted)' }}>
        <span>0%</span>
        <span className="mono font-medium" style={{ color }}>{pct.toFixed(0)}th pct</span>
        <span>100%</span>
      </div>
      <div className="rounded-full h-1.5" style={{ background: 'var(--line)' }}>
        <div
          className="rounded-full h-1.5 transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

function MiniSparkline({ history }: { history: CotItem['history'] }) {
  const values = history.map(h => h.net_noncomm).filter((v): v is number => v !== null);
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const W = 120, H = 32;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - ((v - min) / range) * (H - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const lastVal = values[values.length - 1];
  const prevVal = values[values.length - 2];
  const lineColor = lastVal >= prevVal ? 'var(--up)' : 'var(--down)';

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      <polyline points={pts} fill="none" stroke={lineColor} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

export function CotCard({ item }: { item: CotItem }) {
  const sentimentColor = item.sentiment ? SENTIMENT_COLOR[item.sentiment] : 'var(--muted)';
  const sentimentLabel = item.sentiment ? SENTIMENT_LABEL[item.sentiment] : '—';
  const changeWow = item.change_net_wow;

  return (
    <div
      className="rounded-xl p-4 space-y-3"
      style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              {item.display_name}
            </span>
            {item.exchange && (
              <span className="mono text-xs" style={{ color: 'var(--muted)' }}>
                {item.exchange}
              </span>
            )}
          </div>
          {item.latest_report_date && (
            <span className="text-xs" style={{ color: 'var(--muted)' }}>
              as of {item.latest_report_date}
            </span>
          )}
        </div>
        {item.sentiment && (
          <span
            className="text-xs mono px-2 py-0.5 rounded-full shrink-0"
            style={{ color: sentimentColor, border: `1px solid ${sentimentColor}` }}
          >
            {sentimentLabel}
          </span>
        )}
      </div>

      {/* Net position + change */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <div className="text-xs mb-0.5" style={{ color: 'var(--muted)' }}>Net speculator position</div>
          <div className="mono text-lg font-medium" style={{ color: 'var(--text)' }}>
            {item.net_noncomm !== null ? `${item.net_noncomm > 0 ? '+' : ''}${fmt(item.net_noncomm)}` : 'N/A'}
          </div>
          {changeWow !== null && (
            <div
              className="mono text-xs"
              style={{ color: changeWow >= 0 ? 'var(--up)' : 'var(--down)' }}
            >
              {changeWow >= 0 ? '+' : ''}{fmt(changeWow)} WoW
            </div>
          )}
        </div>
        <MiniSparkline history={item.history} />
      </div>

      {/* Percentile bar */}
      {item.percentile_52w !== null && (
        <PercentileBar value={item.percentile_52w} />
      )}

      {/* Footer stats */}
      <div className="flex gap-4 text-xs" style={{ color: 'var(--muted)' }}>
        {item.net_noncomm_pct_oi !== null && (
          <span>Net/OI: <span className="mono">{item.net_noncomm_pct_oi.toFixed(1)}%</span></span>
        )}
        {item.open_interest !== null && (
          <span>OI: <span className="mono">{fmt(item.open_interest)}</span></span>
        )}
        {item.data_status === 'UNAVAILABLE' && (
          <span style={{ color: 'var(--warn)' }}>UNAVAILABLE — ingestion pending</span>
        )}
      </div>
    </div>
  );
}
