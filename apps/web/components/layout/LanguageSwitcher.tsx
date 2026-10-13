'use client';

import { useTransition } from 'react';
import { setLocale } from '@/app/actions';

const LANGS = [
  { code: 'ro', flag: '🇷🇴', label: 'RO' },
  { code: 'en', flag: '🇺🇸', label: 'EN' },
] as const;

interface Props {
  currentLocale: string;
}

export function LanguageSwitcher({ currentLocale }: Props) {
  const [isPending, startTransition] = useTransition();

  return (
    <div className="flex items-center gap-1 rounded-lg p-1" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
      {LANGS.map(({ code, flag, label }) => {
        const isActive = currentLocale === code;
        return (
          <button
            key={code}
            onClick={() => startTransition(() => setLocale(code))}
            disabled={isPending || isActive}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all"
            style={{
              background: isActive ? 'rgba(61,156,240,0.15)' : 'transparent',
              border: isActive ? '1px solid rgba(61,156,240,0.35)' : '1px solid transparent',
              color: isActive ? 'var(--text)' : 'var(--muted)',
              cursor: isActive ? 'default' : isPending ? 'wait' : 'pointer',
              opacity: isPending && !isActive ? 0.5 : 1,
            }}
            title={code === 'ro' ? 'Română' : 'English'}
          >
            <span style={{ fontSize: '14px', lineHeight: 1 }}>{flag}</span>
            <span className="mono">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
