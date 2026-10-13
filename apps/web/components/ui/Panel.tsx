interface PanelProps {
  title?: string;
  className?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export function Panel({ title, className = '', children, action }: PanelProps) {
  return (
    <div
      className={`rounded-xl ${className}`}
      style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
    >
      {title && (
        <div
          className="flex items-center justify-between px-4 py-3"
          style={{ borderBottom: '1px solid var(--line)' }}
        >
          <span className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
            {title}
          </span>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
