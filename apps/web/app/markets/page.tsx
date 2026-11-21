import { getTranslations } from 'next-intl/server';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { WatchlistTable, type WatchlistItem } from '@/components/market/WatchlistTable';
import { AutoRefresh } from '@/components/ui/AutoRefresh';
import { serverFetch } from '@/lib/server-api';

interface WatchlistResponse {
  items: WatchlistItem[];
  as_of: string;
}

const CATEGORY_KEYS: Record<string, string> = {
  commodity: 'commodities',
  equity: 'equities',
  fx: 'fx',
};

export default async function MarketsPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const t = await getTranslations('market');
  const data = await serverFetch<WatchlistResponse>('/api/market/watchlist');
  const items = data?.items ?? [];

  const groups = Object.entries(CATEGORY_KEYS).map(([cat, labelKey]) => ({
    cat,
    label: t(labelKey as any),
    items: items.filter(i => i.category === cat),
  }));

  const asOf = data?.as_of ? new Date(data.as_of).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC', timeZoneName: 'short' }) : null;

  return (
    <AppShell title={t('title')}>
      <AutoRefresh seconds={60} />
      <div className="p-5 space-y-5">

        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {t('subtitle')}
            </p>
          </div>
          {asOf && (
            <span className="mono text-xs" style={{ color: 'var(--muted)' }}>
              {t('asOf')} {asOf}
            </span>
          )}
        </div>

        {/* Column headers */}
        <div
          className="grid px-4 py-2 rounded-lg text-xs uppercase tracking-wider"
          style={{
            gridTemplateColumns: '160px 1fr 1fr 1.4fr auto',
            gap: '8px',
            color: 'var(--muted)',
            background: 'var(--panel)',
            border: '1px solid var(--line)',
          }}
        >
          <span>{t('instrument')}</span>
          <span className="text-right">{t('lastPrice')}</span>
          <span className="text-right">{t('change1d')}</span>
          <span className="text-right">{t('date')}</span>
          <span className="text-right">{t('status')}</span>
        </div>

        {/* Watchlist grouped by category */}
        <Panel>
          {groups.map(({ cat, label, items: groupItems }) =>
            groupItems.length > 0 ? (
              <WatchlistTable key={cat} items={groupItems} categoryLabel={label} />
            ) : null
          )}
          {items.length === 0 && (
            <div className="p-8 text-center">
              <span className="text-sm" style={{ color: 'var(--muted)' }}>
                {t('noData')}
              </span>
            </div>
          )}
        </Panel>

        {/* Attribution */}
        <p className="text-xs" style={{ color: 'var(--muted)', opacity: 0.6 }}>
          {t('attribution')}
        </p>

      </div>
    </AppShell>
  );
}
