import { DataStatusBadge } from '@/components/ui/Badge';
import type { DataStatus } from '@/types';

interface WatchlistItem {
  series_id: string;
  display_name: string;
  category: string;
  units: string;
  data_status: string;
  latest_date: string | null;
  latest_value: number | null;
  change: number | null;
  change_pct: number | null;
  source_url: string;
}

interface WatchlistTableProps {
  items: WatchlistItem[];
  categoryLabel: string;
}

function fmtValue(value: number | null, units: string): string {
  if (value === null) return '—';
  const u = units.toLowerCase();
  if (u.includes('percent')) return `${value.toFixed(2)}%`;
  if (u.includes('index')) {
    return value >= 1000
      ? value.toLocaleString('en-US', { maximumFractionDigits: 0 })
      : value.toFixed(2);
  }
  if (u.includes('jpy') || u.includes('cny')) return value.toFixed(2);
  if (value >= 100) return value.toFixed(2);
  return value.toFixed(4);
}

function ChangeCell({ change, pct }: { change: number | null; pct: number | null }) {
  if (change === null || pct === null) return <span style={{ color: 'var(--muted)' }}>—</span>;
  const up = change >= 0;
  const color = up ? 'var(--up)' : 'var(--down)';
  const sign = up ? '+' : '';
  return (
    <span className="mono text-xs" style={{ color }}>
      {sign}{change >= 0 ? change.toFixed(4).replace(/\.?0+$/, '').replace(/^(\d+\.\d{2})\d+$/, '$1') : Math.abs(change).toFixed(4).replace(/\.?0+$/, '').replace(/^(\d+\.\d{2})\d+$/, '-$1')}
      {' '}
      <span style={{ opacity: 0.75 }}>({sign}{pct.toFixed(2)}%)</span>
    </span>
  );
}

export function WatchlistTable({ items, categoryLabel }: WatchlistTableProps) {
  return (
    <div>
      {/* Category header */}
      <div
        className="px-4 py-2 text-xs uppercase tracking-widest"
        style={{ color: 'var(--muted)', borderBottom: '1px solid var(--line)', background: 'rgba(42,51,64,0.3)' }}
      >
        {categoryLabel}
      </div>

      {/* Rows */}
      {items.map((item, idx) => (
        <div
          key={item.series_id}
          className="grid items-center px-4 py-3"
          style={{
            gridTemplateColumns: '140px 1fr 1fr 1fr auto',
            gap: '8px',
            borderBottom: idx < items.length - 1 ? '1px solid var(--line)' : undefined,
          }}
        >
          {/* Name */}
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              {item.display_name}
            </span>
            <span className="mono text-xs" style={{ color: 'var(--muted)', opacity: 0.6 }}>
              {item.series_id}
            </span>
          </div>

          {/* Value */}
          <span className="mono text-sm font-semibold text-right" style={{ color: 'var(--text)' }}>
            {fmtValue(item.latest_value, item.units)}
          </span>

          {/* Change */}
          <div className="text-right">
            <ChangeCell change={item.change} pct={item.change_pct} />
          </div>

          {/* Date */}
          <span className="mono text-xs text-right" style={{ color: 'var(--muted)' }}>
            {item.latest_date ?? '—'}
          </span>

          {/* Status + source */}
          <div className="flex flex-col items-end gap-0.5">
            <DataStatusBadge status={item.data_status as DataStatus} />
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs"
              style={{ color: 'var(--accent)', opacity: 0.6 }}
            >
              FRED ↗
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
