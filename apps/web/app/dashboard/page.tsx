import { getTranslations } from 'next-intl/server';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { StatusTile } from '@/components/ui/StatusTile';
import { DataStatusBadge } from '@/components/ui/Badge';

export default async function DashboardPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const t = await getTranslations();

  const REGIME_TILES = [
    { key: 'growth',      label: t('commandCenter.regime.growth') },
    { key: 'inflation',   label: t('commandCenter.regime.inflation') },
    { key: 'liquidity',   label: t('commandCenter.regime.liquidity') },
    { key: 'rates',       label: t('commandCenter.regime.rates') },
    { key: 'usd',         label: t('commandCenter.regime.usd') },
    { key: 'riskAppetite',label: t('commandCenter.regime.riskAppetite') },
    { key: 'credit',      label: t('commandCenter.regime.credit') },
  ];

  const MARKET_TAPE = [
    { label: 'S&P 500',    symbol: 'SPX' },
    { label: 'Nasdaq-100', symbol: 'NDX' },
    { label: 'Gold',       symbol: 'XAU/USD' },
    { label: 'WTI Crude',  symbol: 'CL1' },
    { label: 'Brent',      symbol: 'BRN1' },
    { label: '10Y UST',    symbol: 'DGS10' },
    { label: 'EUR/USD',    symbol: 'EURUSD' },
    { label: 'USD/JPY',    symbol: 'USDJPY' },
  ];

  return (
    <AppShell title={t('commandCenter.title')}>
      <div className="p-5 space-y-5">

        {/* Phase notice */}
        <div
          className="flex items-start gap-3 px-4 py-3 rounded-xl text-sm"
          style={{ background: 'rgba(61,156,240,0.07)', border: '1px solid rgba(61,156,240,0.2)' }}
        >
          <span className="mono font-bold text-xs mt-0.5" style={{ color: 'var(--accent)' }}>
            {t('commandCenter.phaseLabel', { phase: '1' })}
          </span>
          <span style={{ color: 'var(--muted)' }}>{t('commandCenter.phaseNote')}</span>
        </div>

        {/* Market tape */}
        <div
          className="flex items-center gap-0 overflow-x-auto rounded-xl"
          style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
        >
          <span className="px-3 py-2.5 text-xs uppercase tracking-widest flex-shrink-0" style={{ color: 'var(--muted)', borderRight: '1px solid var(--line)' }}>
            {t('commandCenter.marketTape')}
          </span>
          {MARKET_TAPE.map(({ label, symbol }) => (
            <div
              key={symbol}
              className="flex flex-col px-4 py-2 flex-shrink-0"
              style={{ borderRight: '1px solid var(--line)' }}
            >
              <span className="text-xs" style={{ color: 'var(--muted)' }}>{label}</span>
              <span className="mono text-sm font-medium mt-0.5" style={{ color: 'var(--muted)' }}>—</span>
            </div>
          ))}
          <div className="px-3 py-2 ml-auto flex-shrink-0">
            <DataStatusBadge status="UNAVAILABLE" />
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Regime panel */}
          <div className="lg:col-span-2">
            <Panel title={t('commandCenter.marketRegime')}>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4">
                {REGIME_TILES.map(({ key, label }) => (
                  <StatusTile
                    key={key}
                    label={label}
                    value={null}
                    status="unknown"
                    subtext={t('common.unavailable')}
                  />
                ))}
              </div>
            </Panel>
          </div>

          {/* What changed panel */}
          <Panel title={t('commandCenter.whatChanged')}>
            <div className="p-4 flex flex-col items-center justify-center min-h-40">
              <span className="text-xs" style={{ color: 'var(--muted)' }}>
                {t('common.noData')}
              </span>
              <span className="text-xs mt-1" style={{ color: 'var(--muted)', opacity: 0.6 }}>
                {t('commandCenter.phaseNote')}
              </span>
            </div>
          </Panel>
        </div>

        {/* Active scenarios + opportunities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Panel title={t('commandCenter.activeScenarios')}>
            <div className="p-4 flex items-center justify-center min-h-32">
              <span className="text-xs" style={{ color: 'var(--muted)' }}>{t('common.noData')}</span>
            </div>
          </Panel>
          <Panel title={t('commandCenter.topOpportunities')}>
            <div className="p-4 flex items-center justify-center min-h-32">
              <span className="text-xs" style={{ color: 'var(--muted)' }}>{t('common.noData')}</span>
            </div>
          </Panel>
        </div>

      </div>
    </AppShell>
  );
}
