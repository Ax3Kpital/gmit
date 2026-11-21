type DataStatus = 'REALTIME' | 'DELAYED' | 'END_OF_DAY' | 'PERIODIC_OFFICIAL_RELEASE' | 'INDICATIVE' | 'STALE' | 'UNAVAILABLE' | 'UNKNOWN';

const STATUS_STYLES: Record<DataStatus, { bg: string; color: string; text: string }> = {
  REALTIME:                { bg: 'rgba(62,207,142,0.12)', color: 'var(--up)',     text: 'LIVE' },
  DELAYED:                 { bg: 'rgba(230,184,76,0.12)',  color: 'var(--warn)',  text: 'DLY' },
  END_OF_DAY:              { bg: 'rgba(139,152,168,0.12)', color: 'var(--muted)', text: 'EOD' },
  PERIODIC_OFFICIAL_RELEASE:{ bg: 'rgba(61,156,240,0.12)', color: 'var(--accent)', text: 'OFFICIAL' },
  INDICATIVE:              { bg: 'rgba(139,152,168,0.12)', color: 'var(--muted)', text: 'IND' },
  STALE:                   { bg: 'rgba(230,184,76,0.15)',  color: 'var(--warn)',  text: 'STALE' },
  UNAVAILABLE:             { bg: 'rgba(240,113,120,0.12)', color: 'var(--down)',  text: 'N/A' },
  UNKNOWN:                 { bg: 'rgba(139,152,168,0.12)', color: 'var(--muted)', text: '?' },
};

interface BadgeProps {
  status: DataStatus;
  label?: string;
}

export function DataStatusBadge({ status, label }: BadgeProps) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono font-medium"
      style={{ background: style.bg, color: style.color }}
      title={status}
    >
      {label ?? style.text}
    </span>
  );
}

interface ProviderStatusBadgeProps {
  status: 'configured' | 'unconfigured' | 'ok' | 'degraded' | 'down' | 'unknown';
  label?: string;
}

const PROVIDER_STYLES = {
  configured:   { bg: 'rgba(62,207,142,0.12)',  color: 'var(--up)' },
  unconfigured: { bg: 'rgba(230,184,76,0.12)',  color: 'var(--warn)' },
  ok:           { bg: 'rgba(62,207,142,0.12)',  color: 'var(--up)' },
  degraded:     { bg: 'rgba(230,184,76,0.15)',  color: 'var(--warn)' },
  down:         { bg: 'rgba(240,113,120,0.12)', color: 'var(--down)' },
  unknown:      { bg: 'rgba(139,152,168,0.12)', color: 'var(--muted)' },
};

export function ProviderStatusBadge({ status, label }: ProviderStatusBadgeProps) {
  const style = PROVIDER_STYLES[status] ?? PROVIDER_STYLES.unknown;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ background: style.bg, color: style.color }}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5" style={{ background: style.color }} />
      {label ?? status}
    </span>
  );
}
