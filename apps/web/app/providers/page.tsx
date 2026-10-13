import { getTranslations } from 'next-intl/server';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { ProviderStatusBadge } from '@/components/ui/Badge';

interface Provider {
  code: string;
  name: string;
  description: string;
  terms: string;
  phase: number;
  configured: boolean;
  status: string;
  active_phase: boolean;
}

async function fetchProviders(): Promise<Provider[]> {
  try {
    const apiUrl = process.env.API_URL ?? 'http://localhost:8000';
    const res = await fetch(`${apiUrl}/api/providers`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.providers ?? [];
  } catch {
    return [];
  }
}

export default async function ProvidersPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const t = await getTranslations('providers');
  const providers = await fetchProviders();

  return (
    <AppShell title={t('title')}>
      <div className="p-5">
        <p className="text-sm mb-5" style={{ color: 'var(--muted)' }}>
          {t('subtitle')}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {providers.map(p => (
            <div
              key={p.code}
              className="rounded-xl p-4"
              style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
                    {p.name}
                  </p>
                  <p className="text-xs mt-0.5 mono" style={{ color: 'var(--muted)' }}>
                    {p.code}
                  </p>
                </div>
                <ProviderStatusBadge
                  status={p.status as any}
                  label={t(`status.${p.status}` as any)}
                />
              </div>

              {/* Description */}
              <p className="text-xs mb-3" style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                {p.description}
              </p>

              {/* Footer */}
              <div className="flex items-center justify-between">
                <span
                  className="text-xs px-2 py-0.5 rounded mono"
                  style={{ background: 'rgba(61,156,240,0.1)', color: 'var(--accent)', border: '1px solid rgba(61,156,240,0.2)' }}
                >
                  {t('phase', { phase: p.phase })}
                </span>
                {!p.configured && (
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>
                    {p.code === 'fred' || p.code === 'eia' ? t('configureInEnv') : t('noKeyRequired')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
