import { Bell, Search, LogOut } from 'lucide-react';
import { LogoutButton } from './LogoutButton';

interface Props {
  title: string;
}

export function TopBar({ title }: Props) {
  return (
    <header
      className="fixed top-0 right-0 flex items-center justify-between px-5 h-14 z-20"
      style={{
        left: '52px',
        background: 'var(--panel)',
        borderBottom: '1px solid var(--line)',
      }}
    >
      {/* Page title */}
      <h1 className="text-sm font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
        {title}
      </h1>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <button
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors"
          style={{ background: 'var(--input)', border: '1px solid var(--line)', color: 'var(--muted)' }}
        >
          <Search size={13} />
          <span className="hidden sm:block">Search...</span>
          <kbd className="hidden sm:block text-xs px-1 rounded" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            ⌘K
          </kbd>
        </button>

        {/* Alerts bell */}
        <button
          className="relative flex items-center justify-center w-8 h-8 rounded-lg transition-colors"
          style={{ color: 'var(--muted)' }}
          title="Alerts"
        >
          <Bell size={16} strokeWidth={1.75} />
        </button>

        {/* Logout */}
        <LogoutButton />
      </div>
    </header>
  );
}
