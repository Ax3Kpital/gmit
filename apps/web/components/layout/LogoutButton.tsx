'use client';

import { useTransition } from 'react';
import { LogOut } from 'lucide-react';
import { logout } from '@/app/actions';
import { useTranslations } from 'next-intl';

export function LogoutButton() {
  const t = useTranslations('auth');
  const [isPending, startTransition] = useTransition();

  return (
    <button
      onClick={() => startTransition(() => logout())}
      disabled={isPending}
      className="flex items-center justify-center w-8 h-8 rounded-lg transition-colors"
      style={{ color: 'var(--muted)' }}
      title={t('logout')}
    >
      <LogOut size={15} strokeWidth={1.75} />
    </button>
  );
}
