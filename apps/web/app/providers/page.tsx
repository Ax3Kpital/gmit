import { getTranslations } from 'next-intl/server';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { ProviderStatusBadge, DataStatusBadge } from '@/components/ui/Badge';
import { serverFetch } from '@/lib/server-api';
import type { DataStatus } from '@/types';

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

interface HealthItem {
  key: string;
  label: string;
  cadence: string;
  fallback: boolean;
  latest_data: string | null;
  expected: string | null;
  status: string;
  last_fetched_at: string | null;
  next_run_at: string | null;
  detail: string;
}

interface DataHealth {
  as_of: string;
  healthy: boolean;
  attention: string[];
  items: HealthItem[];
}

function hhmm(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return `${d.toISOString().slice(5, 10)} ${d.toISOString().slice(11, 16)}`;
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
  const health = await serverFetch<DataHealth>('/api/data-health');

  return (
    <AppShell title={t('title')}>
      <div className="p-5">
        <p className="text-sm mb-5" style={{ color: 'var(--muted)' }}>
          {t('subtitle')}
        </p>

        {health && (
          <div className="mb-6 rounded-xl overflow-hidden" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid var(--line)' }}>
              <span className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Data freshness</span>
              <span className="text-xs mono" style={{ color: health.healthy ? 'var(--up)' : 'var(--warn)' }}>
                {health.healthy ? 'ALL SOURCES CURRENT' : `ATTENTION: ${health.attention.join(', ')}`}
              </span>
            </div>
            <div className="grid px-4 py-2 text-xs uppercase tracking-wider"
              style={{ gridTemplateColumns: '2.2fr 1fr 1fr 1fr 1fr 1fr', gap: '8px', color: 'var(--muted)', borderBottom: '1px solid var(--line)' }}>
              <span>Source</span><span>Latest data</span><span>Expected</span><span>Status</span><span>Last fetched (UTC)</span><span>Next run (UTC)</span>
            </div>
            {health.items.map(i => (
              <div key={i.key} className="px-4 py-3" style={{ borderBottom: '1px solid var(--line)', opacity: i.fallback ? 0.6 : 1 }}>
                <div className="grid items-center text-xs" style={{ gridTemplateColumns: '2.2fr 1fr 1fr 1fr 1fr 1fr', gap: '8px' }}>
                  <span style={{ color: 'var(--text)' }}>{i.label}{i.fallback ? ' · fallback' : ''}
                    <span className="block mono" style={{ color: 'var(--muted)' }}>{i.cadence}</span></span>
                  <span className="mono" style={{ color: 'var(--text)' }}>{i.latest_data ?? '—'}</span>
                  <span className="mono" style={{ color: 'var(--muted)' }}>{i.expected ?? '—'}</span>
                  <span><DataStatusBadge status={i.status as DataStatus} /></span>
                  <span className="mono" style={{ color: 'var(--muted)' }}>{hhmm(i.last_fetched_at)}</span>
                  <span className="mono" style={{ color: 'var(--muted)' }}>{hhmm(i.next_run_at)}</span>
                </div>
                <p className="mt-1 text-xs" style={{ color: 'var(--muted)', opacity: 0.8 }}>{i.detail}</p>
              </div>
            ))}
          </div>
        )}

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
