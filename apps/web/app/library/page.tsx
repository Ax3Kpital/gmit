import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { getTranslations } from 'next-intl/server';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { LibraryClient } from './LibraryClient';
import { serverFetch } from '@/lib/server-api';

interface ThesisSummary {
  id: string;
  topic: string;
  claim: string;
  confidence: number;
  time_horizon: string;
  provider: string;
  is_demo: boolean;
  created_at: string;
}

export default async function LibraryPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const t = await getTranslations('research');
  const initialTheses = await serverFetch<ThesisSummary[]>('/api/research/theses') ?? [];

  const labels = {
    title: t('title'),
    subtitle: t('subtitle'),
    topicPlaceholder: t('topicPlaceholder'),
    generate: t('generate'),
    generating: t('generating'),
    errorEmpty: t('errorEmpty'),
    errorFailed: t('errorFailed'),
    noTheses: t('noTheses'),
    aiDisclaimer: t('aiDisclaimer'),
    demoNotice: t('demoNotice'),
  };

  return (
    <AppShell title={t('title')}>
      <div className="p-5 space-y-5 max-w-4xl mx-auto">

        <div>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            {labels.subtitle}
          </p>
        </div>

        {/* Create form + thesis list (client island) */}
        <LibraryClient initialTheses={initialTheses} labels={labels} />

        {/* Disclaimer */}
        <p className="text-xs" style={{ color: 'var(--muted)', opacity: 0.55 }}>
          {labels.aiDisclaimer}
        </p>

      </div>
    </AppShell>
  );
}
