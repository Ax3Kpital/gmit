'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  LayoutDashboard, TrendingUp, BarChart2, Globe, GitBranch,
  Lightbulb, Brain, Bell, BookOpen, Activity, Database, Settings,
} from 'lucide-react';

const NAV_ITEMS = [
  { key: 'commandCenter',   href: '/dashboard',   icon: LayoutDashboard },
  { key: 'markets',         href: '/markets',     icon: TrendingUp },
  { key: 'macro',           href: '/macro',       icon: BarChart2 },
  { key: 'geopolitics',     href: '/geopolitics', icon: Globe },
  { key: 'scenarios',       href: '/scenarios',   icon: GitBranch },
  { key: 'opportunities',   href: '/opportunities', icon: Lightbulb },
  { key: 'smartMoney',      href: '/smart-money', icon: Brain },
  { key: 'alerts',          href: '/alerts',      icon: Bell },
  { key: 'researchLibrary', href: '/library',     icon: BookOpen },
  { key: 'agentActivity',   href: '/agents',      icon: Activity },
] as const;

const BOTTOM_ITEMS = [
  { key: 'providers', href: '/providers', icon: Database },
  { key: 'settings',  href: '/settings',  icon: Settings },
] as const;

export function Sidebar() {
  const t = useTranslations('nav');
  const pathname = usePathname();

  const isActive = (href: string) => pathname === href || (href !== '/dashboard' && pathname.startsWith(href));

  return (
    <nav
      className="fixed left-0 top-0 h-full flex flex-col z-30"
      style={{
        width: '52px',
        background: 'var(--panel)',
        borderRight: '1px solid var(--line)',
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center justify-center h-14 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--line)' }}
      >
        <span className="mono font-bold text-sm" style={{ color: 'var(--accent)' }}>
          G
        </span>
      </div>

      {/* Main nav */}
      <div className="flex-1 overflow-y-auto py-2">
        {NAV_ITEMS.map(({ key, href, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              title={t(key as any)}
              className="flex items-center justify-center h-10 mx-1.5 my-0.5 rounded-lg transition-colors group relative"
              style={{
                background: active ? 'rgba(61,156,240,0.12)' : 'transparent',
                color: active ? 'var(--accent)' : 'var(--muted)',
              }}
            >
              <Icon size={17} strokeWidth={1.75} />
              {/* Tooltip */}
              <span
                className="absolute left-full ml-2.5 px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none z-50 transition-opacity"
                style={{ background: 'var(--panel)', border: '1px solid var(--line)', color: 'var(--text)' }}
              >
                {t(key as any)}
              </span>
              {/* Active indicator */}
              {active && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r"
                  style={{ background: 'var(--accent)' }}
                />
              )}
            </Link>
          );
        })}
      </div>

      {/* Bottom nav */}
      <div className="py-2" style={{ borderTop: '1px solid var(--line)' }}>
        {BOTTOM_ITEMS.map(({ key, href, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              title={t(key as any)}
              className="flex items-center justify-center h-10 mx-1.5 my-0.5 rounded-lg transition-colors group relative"
              style={{
                background: active ? 'rgba(61,156,240,0.12)' : 'transparent',
                color: active ? 'var(--accent)' : 'var(--muted)',
              }}
            >
              <Icon size={17} strokeWidth={1.75} />
              <span
                className="absolute left-full ml-2.5 px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none z-50 transition-opacity"
                style={{ background: 'var(--panel)', border: '1px solid var(--line)', color: 'var(--text)' }}
              >
                {t(key as any)}
              </span>
              {active && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r"
                  style={{ background: 'var(--accent)' }}
                />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
