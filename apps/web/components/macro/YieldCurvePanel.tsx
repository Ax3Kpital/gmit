import { getTranslations } from 'next-intl/server';
import { serverFetch } from '@/lib/server-api';
import { Panel } from '@/components/ui/Panel';
import { DataStatusBadge } from '@/components/ui/Badge';
import type { MacroSeriesResponse, MacroObservationPoint, DataStatus } from '@/types';

const SERIES = [
  { id: 'DGS10',  labelKey: 'dgs10'  },
  { id: 'DGS2',   labelKey: 'dgs2'   },
  { id: 'T10Y2Y', labelKey: 'spread' },
] as const;

function Sparkline({ data }: { data: MacroObservationPoint[] }) {
  const valid = data.filter((d): d is { date: string; value: number } => d.value !== null);
  if (valid.length < 2) return <div className="w-full h-10" />;

  const W = 240, H = 40;
  const vals = valid.map(d => d.value);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 0.001;

  const pts = valid
    .map((d, i) => {
      const x = (i / (valid.length - 1)) * W;
      const y = H - 2 - ((d.value - min) / range) * (H - 4);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-10" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts} fill="none" stroke="var(--accent)" strokeWidth="1.5"
        strokeLinejoin="round" strokeLinecap="round" opacity="0.8" />
    </svg>
  );
}

function getDelta(history: MacroObservationPoint[]): number | null {
  const valid = history.filter((d): d is { date: string; value: number } => d.value !== null);
  if (valid.length < 10) return null;
  return valid[valid.length - 1].value - valid[Math.max(0, valid.length - 30)].value;
}

function fmt(v: number | null | undefined, units: string): string {
  if (v == null) return '—';
  return units.toLowerCase().includes('percent') ? `${v.toFixed(2)}%` : v.toFixed(2);
}

interface SeriesCardProps {
  label: string;
  data: MacroSeriesResponse | null;
  last?: boolean;
}

function SeriesCard({ label, data, last }: SeriesCardProps) {
  const delta = data ? getDelta(data.history) : null;
  const status = (data?.data_status ?? 'UNAVAILABLE') as DataStatus;

  return (
    <div
      className="flex flex-col gap-1 p-4"
      style={last ? undefined : { borderRight: '1px solid var(--line)' }}
    >
      <span className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
        {label}
      </span>

      <span className="mono text-2xl font-semibold leading-tight" style={{ color: 'var(--text)' }}>
        {fmt(data?.latest?.value, data?.units ?? '')}
      </span>

      {delta !== null && (
        <span className="mono text-xs" style={{ color: delta >= 0 ? 'var(--up)' : 'var(--down)' }}>
          {delta >= 0 ? '+' : ''}{delta.toFixed(2)} 1mo
        </span>
      )}

      <div className="mt-1">
        {data?.history && data.history.length > 1 ? (
          <Sparkline data={data.history.slice(-90)} />
        ) : (
          <div className="w-full h-10 flex items-center justify-center">
            <span className="text-xs" style={{ color: 'var(--muted)' }}>—</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-1">
        <DataStatusBadge status={status} />
        {data?.latest?.date && (
          <span className="mono text-xs" style={{ color: 'var(--muted)' }}>{data.latest.date}</span>
        )}
      </div>

      {data?.source_url && (
        <a href={data.source_url} target="_blank" rel="noopener noreferrer"
          className="text-xs mt-0.5" style={{ color: 'var(--accent)', opacity: 0.7 }}>
          {data.latest?.provider?.startsWith('us_treasury') ? 'US Treasury' : 'FRED'} ↗
        </a>
      )}
    </div>
  );
}

export async function YieldCurvePanel() {
  const t = await getTranslations('macro');

  const results = await Promise.all(
    SERIES.map(s => serverFetch<MacroSeriesResponse>(`/api/macro/series/${s.id}`))
  );

  return (
    <Panel title={t('title')}>
      <div className="grid grid-cols-1 sm:grid-cols-3">
        {SERIES.map((s, i) => (
          <SeriesCard
            key={s.id}
            label={t(s.labelKey)}
            data={results[i]}
            last={i === SERIES.length - 1}
          />
        ))}
      </div>
    </Panel>
  );
}
