import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { GprChart } from '@/components/geo/GprChart';
import { serverFetch } from '@/lib/server-api';

const RISK_COLOR: Record<string, string> = {
  critical: '#f07178',
  elevated:  '#e6b84c',
  moderate:  '#3d9cf0',
  low:       '#3ecf8e',
  unknown:   '#8b98a8',
};

interface GeoRegion {
  region_key: string;
  region_label: string;
  risk_level: string;
  risk_score: number;
  avg_tone: number | null;
  article_count: number | null;
  note: string;
  data_status: string;
  event_date: string | null;
  retrieved_at: string | null;
  articles: Array<{
    url: string;
    title: string | null;
    domain: string | null;
    source_country: string | null;
    published_at: string | null;
  }>;
}

interface GprPoint {
  period: string;
  gpr_value: number | null;
  gpr_threat: number | null;
  gpr_act: number | null;
}

interface RiskSummaryResponse {
  regions: GeoRegion[];
}

interface RiskIndexResponse {
  series: GprPoint[];
  data_status: string;
  latest_period: string | null;
}

function RiskBar({ score }: { score: number }) {
  const level = score >= 72 ? 'critical' : score >= 52 ? 'elevated' : score >= 32 ? 'moderate' : 'low';
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 rounded-full overflow-hidden" style={{ background: 'var(--line)', height: 3 }}>
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${score}%`, background: RISK_COLOR[level] }}
        />
      </div>
      <span className="text-xs mono w-8 text-right" style={{ color: RISK_COLOR[level] }}>
        {score.toFixed(0)}
      </span>
    </div>
  );
}

function ArticleLink({ art }: { art: GeoRegion['articles'][0] }) {
  const title = art.title ?? art.domain ?? art.url;
  const display = title.length > 80 ? title.slice(0, 77) + '…' : title;
  return (
    <a
      href={art.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block text-xs leading-snug py-0.5 hover:opacity-80 transition-opacity"
      style={{ color: 'var(--accent)' }}
    >
      {display}
      {art.domain && (
        <span className="ml-1 mono" style={{ color: 'var(--muted)' }}>
          ({art.domain})
        </span>
      )}
    </a>
  );
}

export default async function GeopoliticsPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const [riskData, indexData] = await Promise.all([
    serverFetch<RiskSummaryResponse>('/api/geo/risk-summary'),
    serverFetch<RiskIndexResponse>('/api/geo/risk-index?months=36'),
  ]);

  const regions = riskData?.regions ?? [];
  const hasLiveData = regions.some(r => r.data_status !== 'UNAVAILABLE');

  // Sort: critical → elevated → moderate → low
  const ORDER = { critical: 0, elevated: 1, moderate: 2, low: 3, unknown: 4 };
  const sorted = [...regions].sort(
    (a, b) => (ORDER[a.risk_level as keyof typeof ORDER] ?? 4) - (ORDER[b.risk_level as keyof typeof ORDER] ?? 4)
  );

  const gprSeries = indexData?.series ?? [];
  const gprStatus = indexData?.data_status ?? 'UNAVAILABLE';
  const gprLatestPeriod = indexData?.latest_period;

  return (
    <AppShell title="Geopolitică">
      <div className="p-5 space-y-5 max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Geopolitical risk monitoring — GDELT news tone + GPR Index (Caldara &amp; Iacoviello).
          </p>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className="text-xs px-2 py-0.5 rounded-full mono"
              style={{
                background: hasLiveData ? 'rgba(61,156,240,0.1)' : 'var(--line)',
                color: hasLiveData ? 'var(--accent)' : 'var(--muted)',
                border: hasLiveData ? '1px solid rgba(61,156,240,0.3)' : '1px solid var(--line)',
              }}
            >
              {hasLiveData ? 'LIVE — GDELT' : 'MANUAL FALLBACK'}
            </span>
          </div>
        </div>

        {/* Regional risk matrix */}
        <div>
          <h3 className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--muted)' }}>
            Regional Risk Assessment
          </h3>
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--line)' }}>
            {sorted.map((r, i) => (
              <div
                key={r.region_key}
                className="px-5 py-4"
                style={{
                  borderBottom: i < sorted.length - 1 ? '1px solid var(--line)' : 'none',
                  background: i % 2 === 0 ? 'var(--panel)' : 'var(--bg)',
                }}
              >
                <div className="flex items-start gap-4">
                  <span
                    className="text-xs mono px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5 uppercase"
                    style={{ color: RISK_COLOR[r.risk_level] ?? RISK_COLOR.unknown, border: `1px solid ${(RISK_COLOR[r.risk_level] ?? RISK_COLOR.unknown)}33` }}
                  >
                    {r.risk_level}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium mb-0.5" style={{ color: 'var(--text)' }}>
                      {r.region_label}
                    </div>
                    <div className="text-xs mb-1" style={{ color: 'var(--muted)' }}>{r.note}</div>
                    <RiskBar score={r.risk_score} />

                    {/* Articles */}
                    {r.articles.length > 0 && (
                      <div className="mt-2 space-y-0.5">
                        {r.articles.slice(0, 3).map((art, j) => (
                          <ArticleLink key={j} art={art} />
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Stats */}
                  {r.avg_tone !== null && (
                    <div className="flex-shrink-0 text-right">
                      <div className="text-xs mono" style={{ color: r.avg_tone < -2 ? 'var(--down)' : r.avg_tone > 1 ? 'var(--up)' : 'var(--muted)' }}>
                        tone {r.avg_tone > 0 ? '+' : ''}{r.avg_tone.toFixed(1)}
                      </div>
                      {r.article_count !== null && (
                        <div className="text-xs mono mt-0.5" style={{ color: 'var(--muted)' }}>
                          {r.article_count.toLocaleString()} art/wk
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {regions.length > 0 && regions[0].retrieved_at && (
            <p className="text-xs mt-1 mono" style={{ color: 'var(--muted)', opacity: 0.55 }}>
              Updated {new Date(regions[0].retrieved_at).toLocaleString()} · Source: GDELT 2.0 (gdeltproject.org)
            </p>
          )}
        </div>

        {/* GPR Index chart */}
        <div className="rounded-xl p-5" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                Geopolitical Risk Index (GPR)
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                Caldara &amp; Iacoviello — monthly index, 100 = long-run average. Threat vs. Acts components.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="text-xs mono px-2 py-0.5 rounded"
                style={{ background: 'var(--line)', color: 'var(--muted)' }}
              >
                {gprStatus === 'PERIODIC_OFFICIAL_RELEASE' ? 'OFFICIAL' : gprStatus}
              </span>
              {gprLatestPeriod && (
                <span className="text-xs mono" style={{ color: 'var(--muted)' }}>
                  through {new Date(gprLatestPeriod).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                </span>
              )}
            </div>
          </div>
          <GprChart series={gprSeries} />
          {gprSeries.length === 0 && (
            <p className="text-xs mt-2 mono" style={{ color: 'var(--muted)', opacity: 0.6 }}>
              GPR data loads on first backend startup. Refresh in ~30 seconds.
            </p>
          )}
          <p className="text-xs mt-3" style={{ color: 'var(--muted)', opacity: 0.5 }}>
            Source: matteoiacoviello.com/gpr.htm · Updated monthly · 100 = 1985–2019 average
          </p>
        </div>

        {/* Market impact */}
        <div className="rounded-xl p-5" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
          <h3 className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--muted)' }}>
            Market Impact Monitor
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: 'Energy premium (geopolitical)',  desc: 'Brent vs fundamental price model — war risk premium embedded in crude' },
              { label: 'Gold safe-haven flow',           desc: 'COT extreme long as proxy for geopolitical flight to safety' },
              { label: 'Defense sector relative',        desc: 'ITA/XAR vs SPX — institutional rotation into defense spending' },
            ].map(item => (
              <div key={item.label} className="rounded-lg p-3"
                style={{ background: 'var(--bg)', border: '1px solid var(--line)' }}>
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text)' }}>{item.label}</div>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>{item.desc}</p>
                <div className="mt-2 text-xs mono" style={{ color: 'var(--line)' }}>PHASE 9 — instrument data feed</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </AppShell>
  );
}
