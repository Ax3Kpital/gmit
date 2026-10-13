interface StatusTileProps {
  label: string;
  value?: string | null;
  subtext?: string;
  status?: 'ok' | 'warn' | 'down' | 'unknown';
  className?: string;
}

const STATUS_COLOR = {
  ok:      'var(--up)',
  warn:    'var(--warn)',
  down:    'var(--down)',
  unknown: 'var(--muted)',
};

export function StatusTile({ label, value, subtext, status = 'unknown', className = '' }: StatusTileProps) {
  const color = STATUS_COLOR[status];

  return (
    <div
      className={`rounded-xl p-4 ${className}`}
      style={{ background: 'var(--input)', border: '1px solid var(--line)' }}
    >
      <p className="text-xs uppercase tracking-widest mb-2" style={{ color: 'var(--muted)' }}>
        {label}
      </p>
      {value ? (
        <p className="text-xl font-semibold mono tracking-tight" style={{ color }}>
          {value}
        </p>
      ) : (
        <p className="text-xl font-semibold mono" style={{ color: 'var(--muted)' }}>
          —
        </p>
      )}
      {subtext && (
        <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
          {subtext}
        </p>
      )}
    </div>
  );
}
