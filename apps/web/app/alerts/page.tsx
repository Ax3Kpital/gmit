import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Panel } from '@/components/ui/Panel';
import { serverFetch } from '@/lib/server-api';
import { AlertsClient } from './AlertsClient';

interface AlertEvent {
  id: string;
  rule_id: string;
  triggered_at: string;
  message: string;
  value_at_trigger: number | null;
  threshold_value: number;
  acknowledged: boolean;
  acknowledged_at: string | null;
}

interface AlertRule {
  id: string;
  name: string;
  rule_type: string;
  series_id: string | null;
  cftc_code: string | null;
  condition: string;
  threshold_value: number;
  enabled: boolean;
  created_at: string;
}

export default async function AlertsPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const [events, rules] = await Promise.all([
    serverFetch<AlertEvent[]>('/api/alerts/events') ?? [],
    serverFetch<AlertRule[]>('/api/alerts/rules') ?? [],
  ]);

  return (
    <AppShell title="Alerts">
      <div className="p-5 space-y-5 max-w-4xl mx-auto">
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Price threshold and COT extreme positioning alerts
        </p>
        <AlertsClient
          initialEvents={events ?? []}
          initialRules={rules ?? []}
        />
      </div>
    </AppShell>
  );
}
