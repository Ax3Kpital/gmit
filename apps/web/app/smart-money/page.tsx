import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { getTranslations } from 'next-intl/server';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { CotCard, type CotItem } from '@/components/smart_money/CotCard';
import { serverFetch } from '@/lib/server-api';
import { DataStatusBadge } from '@/components/ui/Badge';
import type { DataStatus } from '@/types';

interface CotRelease {
  positions_as_of: string;
  published_at: string;
  next_positions_as_of: string;
  next_release_at: string;
  data_status: string;
  cadence: string;
}

function fmtUtc(iso: string): string {
  const d = new Date(iso);
  const day = d.toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' });
  return `${day} ${d.toISOString().slice(0, 10)} ${d.toISOString().slice(11, 16)} UTC`;
}

interface CotResponse {
  release: CotRelease | null;
  items: CotItem[];
  source: string;
  lag_note: string;
}

const CATEGORY_ORDER = ['commodity', 'equity', 'rates', 'fx'];
const CATEGORY_LABELS: Record<string, string> = {
  commodity: 'Commodities',
  equity: 'Equities',
  rates: 'Rates',
  fx: 'FX',
};

export default async function SmartMoneyPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const data = await serverFetch<CotResponse>('/api/smart-money/cot');
  const items = data?.items ?? [];

  const grouped = CATEGORY_ORDER.map(cat => ({
    cat,
    label: CATEGORY_LABELS[cat],
    items: items.filter(i => i.category === cat),
  })).filter(g => g.items.length > 0);

  return (
    <AppShell title="Smart Money">
      <div className="p-5 space-y-6 max-w-5xl mx-auto">

        <div>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            CFTC Commitments of Traders — speculator net positioning + 52-week percentile
          </p>
          {data?.release && (
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg px-3 py-2 text-xs"
              style={{ background: 'var(--panel)', border: '1px solid var(--line)', color: 'var(--muted)' }}>
              <DataStatusBadge status={data.release.data_status as DataStatus} />
              <span>Weekly data: positions as of <b style={{ color: 'var(--text)' }}>{data.release.positions_as_of}</b></span>
              <span>published {fmtUtc(data.release.published_at)}</span>
              <span>next report (positions {data.release.next_positions_as_of}) expected <b style={{ color: 'var(--text)' }}>{fmtUtc(data.release.next_release_at)}</b></span>
            </div>
          )}
        </div>

        {items.length === 0 && (
          <Panel>
            <div className="p-10 text-center">
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                COT data is being fetched for the first time. Check back in a moment.
              </p>
            </div>
          </Panel>
        )}

        {grouped.map(({ cat, label, items: groupItems }) => (
          <div key={cat} className="space-y-3">
            <h3 className="text-xs uppercase tracking-wider font-medium" style={{ color: 'var(--muted)' }}>
              {label}
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {groupItems.map(item => (
                <CotCard key={item.cftc_code} item={item} />
              ))}
            </div>
          </div>
        ))}

        {data && (
          <p className="text-xs" style={{ color: 'var(--muted)', opacity: 0.55 }}>
            {data.source}. {data.lag_note} Published Fridays ~3:30 PM ET.
          </p>
        )}

        {/* SEC 13F stub */}
        <div
          className="rounded-xl p-5"
          style={{ background: 'var(--panel)', border: '1px solid var(--line)', opacity: 0.6 }}
        >
          <div className="flex items-center gap-3">
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: 'var(--line)', color: 'var(--muted)' }}
            >
              COMING PHASE 5b
            </span>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>
              SEC 13F Institutional Holdings — quarterly filings, 45-day lag. Parsing pipeline in progress.
            </span>
          </div>
        </div>

      </div>
    </AppShell>
  );
}
