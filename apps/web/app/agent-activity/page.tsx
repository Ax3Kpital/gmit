import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { serverFetch } from '@/lib/server-api';

interface AgentRun {
  id: string;
  agent_type: string;
  trigger: string | null;
  status: string;
  provider: string | null;
  model_name: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  duration_ms: number | null;
  result_summary: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

const STATUS_COLOR: Record<string, string> = {
  completed: 'var(--up)',
  running: 'var(--accent)',
  failed: 'var(--down)',
};

const TYPE_LABEL: Record<string, string> = {
  daily_briefing: 'Daily Briefing',
  thesis: 'Thesis Generation',
  cot_ingestion: 'COT Ingestion',
  fred_ingestion: 'FRED Ingestion',
};

function fmtDuration(ms: number | null) {
  if (ms === null) return '—';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function fmtTime(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default async function AgentActivityPage() {
  const session = cookies().get('gmit_session');
  if (!session) redirect('/login');

  const runs = await serverFetch<AgentRun[]>('/api/agent-runs?limit=100') ?? [];

  const stats = {
    total: runs.length,
    completed: runs.filter(r => r.status === 'completed').length,
    failed: runs.filter(r => r.status === 'failed').length,
    totalTokens: runs.reduce((s, r) => s + (r.input_tokens ?? 0) + (r.output_tokens ?? 0), 0),
  };

  return (
    <AppShell title="AI Agents">
      <div className="p-5 space-y-5 max-w-6xl mx-auto">

        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          All agent runs — thesis generation, daily briefing, ingestion jobs
        </p>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total runs', value: stats.total },
            { label: 'Completed', value: stats.completed, color: 'var(--up)' },
            { label: 'Failed', value: stats.failed, color: stats.failed > 0 ? 'var(--down)' : 'var(--muted)' },
            { label: 'Tokens used', value: stats.totalTokens.toLocaleString() },
          ].map(s => (
            <div key={s.label} className="rounded-xl p-4"
              style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
              <div className="text-xs mb-1" style={{ color: 'var(--muted)' }}>{s.label}</div>
              <div className="mono text-xl font-semibold" style={{ color: s.color ?? 'var(--text)' }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>

        {/* Runs table */}
        {runs.length === 0 ? (
          <div className="rounded-xl p-10 text-center" style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>No agent runs recorded yet.</p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--line)' }}>
            <table className="w-full text-xs">
              <thead>
                <tr style={{ background: 'var(--panel)', borderBottom: '1px solid var(--line)' }}>
                  {['Type', 'Trigger', 'Status', 'Provider', 'Tokens', 'Duration', 'Started'].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium"
                      style={{ color: 'var(--muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runs.map((run, i) => (
                  <tr
                    key={run.id}
                    style={{
                      background: i % 2 === 0 ? 'var(--panel)' : 'var(--bg)',
                      borderBottom: '1px solid var(--line)',
                    }}
                  >
                    <td className="px-4 py-3 font-medium" style={{ color: 'var(--text)' }}>
                      {TYPE_LABEL[run.agent_type] ?? run.agent_type}
                    </td>
                    <td className="px-4 py-3 mono" style={{ color: 'var(--muted)' }}>
                      {run.trigger ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full mono"
                        style={{
                          color: STATUS_COLOR[run.status] ?? 'var(--muted)',
                          border: `1px solid ${STATUS_COLOR[run.status] ?? 'var(--line)'}`,
                        }}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 mono" style={{ color: 'var(--muted)' }}>
                      {run.provider ?? '—'}
                    </td>
                    <td className="px-4 py-3 mono" style={{ color: 'var(--muted)' }}>
                      {run.input_tokens !== null || run.output_tokens !== null
                        ? `${(run.input_tokens ?? 0) + (run.output_tokens ?? 0)}`
                        : '—'}
                    </td>
                    <td className="px-4 py-3 mono" style={{ color: 'var(--muted)' }}>
                      {fmtDuration(run.duration_ms)}
                    </td>
                    <td className="px-4 py-3 mono" style={{ color: 'var(--muted)' }}>
                      {fmtTime(run.started_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Detail: failed runs */}
        {runs.some(r => r.status === 'failed') && (
          <div className="space-y-2">
            <h3 className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
              Failed runs
            </h3>
            {runs.filter(r => r.status === 'failed').map(run => (
              <div key={run.id} className="rounded-xl p-4"
                style={{ background: 'var(--panel)', border: '1px solid var(--down)' }}>
                <div className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  {TYPE_LABEL[run.agent_type] ?? run.agent_type} · {fmtTime(run.started_at)}
                </div>
                <p className="text-xs mono" style={{ color: 'var(--down)' }}>
                  {run.error_message ?? 'Unknown error'}
                </p>
              </div>
            ))}
          </div>
        )}

      </div>
    </AppShell>
  );
}
