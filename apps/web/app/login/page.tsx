'use client';

import { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { login } from '@/app/actions';

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isPending, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    startTransition(async () => {
      const result = await login(email, password);
      if (result.ok) {
        router.push('/dashboard');
        router.refresh();
      } else {
        setError(t('auth.invalidCredentials'));
      }
    });
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: 'var(--bg)' }}>
      {/* Login card */}
      <div
        className="w-full max-w-sm rounded-xl p-8"
        style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
      >
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-accent font-bold text-lg mono">GMIT</span>
            <span
              className="text-xs px-1.5 py-0.5 rounded font-mono"
              style={{ background: 'rgba(61,156,240,0.12)', color: 'var(--accent)', border: '1px solid rgba(61,156,240,0.25)' }}
            >
              v0.1
            </span>
          </div>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {t('app.tagline')}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs mb-1.5" style={{ color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('auth.email')}
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ background: 'var(--input)', border: '1px solid var(--line)', color: 'var(--text)' }}
              placeholder="admin@gmit.local"
            />
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('auth.password')}
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ background: 'var(--input)', border: '1px solid var(--line)', color: 'var(--text)' }}
            />
          </div>

          {error && (
            <p className="text-xs text-down">{error}</p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-opacity"
            style={{
              background: 'var(--accent)',
              color: '#0e1116',
              opacity: isPending ? 0.6 : 1,
              cursor: isPending ? 'not-allowed' : 'pointer',
            }}
          >
            {isPending ? t('auth.signingIn') : t('auth.signIn')}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-6 text-xs text-center" style={{ color: 'var(--muted)' }}>
          {t('app.notFinancialAdvice')}
        </p>
      </div>
    </div>
  );
}
