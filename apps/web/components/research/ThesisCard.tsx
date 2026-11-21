'use client';

interface EvidenceItem {
  id: string;
  description: string;
  series_id: string | null;
  value: number | null;
  obs_date: string | null;
  interpretation: string;
}

interface Scenario {
  id: string;
  name: string;
  probability: number;
  description: string;
  trigger: string;
}

interface CounterArgument {
  id: string;
  argument: string;
  strength: 'weak' | 'moderate' | 'strong';
}

export interface ThesisFull {
  id: string;
  topic: string;
  claim: string;
  confidence: number;
  time_horizon: string;
  rationale: string;
  catalysts: string[];
  invalidation_conditions: string[];
  model_name: string;
  provider: string;
  input_tokens: number | null;
  output_tokens: number | null;
  generation_ms: number | null;
  status: string;
  is_demo: boolean;
  created_at: string;
  evidence_items: EvidenceItem[];
  scenarios: Scenario[];
  counter_arguments: CounterArgument[];
}

const STRENGTH_COLOR: Record<string, string> = {
  weak: 'var(--up)',
  moderate: 'var(--warn)',
  strong: 'var(--down)',
};

function ConfidencePill({ value }: { value: number }) {
  const color = value >= 65 ? 'var(--up)' : value >= 40 ? 'var(--warn)' : 'var(--down)';
  return (
    <span
      className="mono text-xs px-2 py-0.5 rounded-full"
      style={{ color, border: `1px solid ${color}`, opacity: 0.9 }}
    >
      {value}%
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
        {title}
      </h4>
      {children}
    </div>
  );
}

export function ThesisCard({ thesis, expanded = false }: { thesis: ThesisFull; expanded?: boolean }) {
  const created = new Date(thesis.created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });

  return (
    <div
      className="rounded-xl p-5 space-y-5"
      style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
    >
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-xs px-2 py-0.5 rounded-full mono"
              style={{ background: 'var(--line)', color: 'var(--muted)' }}
            >
              {thesis.time_horizon}
            </span>
            <ConfidencePill value={thesis.confidence} />
            {thesis.is_demo && (
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(230,184,76,0.15)', color: 'var(--warn)', border: '1px solid var(--warn)' }}
              >
                DEMO
              </span>
            )}
          </div>
          <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
            {created}
          </span>
        </div>

        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          {thesis.topic}
        </p>

        <p className="text-base font-medium leading-snug" style={{ color: 'var(--text)' }}>
          {thesis.claim}
        </p>
      </div>

      {/* Rationale */}
      <Section title="Rationale">
        <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: 'var(--muted)' }}>
          {thesis.rationale}
        </p>
      </Section>

      {/* Evidence */}
      {thesis.evidence_items.length > 0 && (
        <Section title={`Evidence (${thesis.evidence_items.length})`}>
          <div className="space-y-2">
            {thesis.evidence_items.map(e => (
              <div
                key={e.id}
                className="rounded-lg p-3 space-y-1"
                style={{ background: 'var(--bg)', border: '1px solid var(--line)' }}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                    {e.description}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    {e.series_id && (
                      <span className="mono text-xs" style={{ color: 'var(--muted)' }}>
                        {e.series_id}
                      </span>
                    )}
                    {e.value !== null && (
                      <span className="mono text-xs" style={{ color: 'var(--accent)' }}>
                        {e.value}
                      </span>
                    )}
                    {e.obs_date && (
                      <span className="mono text-xs" style={{ color: 'var(--muted)' }}>
                        {e.obs_date}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>
                  {e.interpretation}
                </p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Scenarios */}
      {thesis.scenarios.length > 0 && (
        <Section title="Scenarios">
          <div className="space-y-2">
            {thesis.scenarios.map(s => (
              <div
                key={s.id}
                className="rounded-lg p-3 space-y-1"
                style={{ background: 'var(--bg)', border: '1px solid var(--line)' }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>
                    {s.name}
                  </span>
                  <span className="mono text-xs" style={{ color: 'var(--accent)' }}>
                    {s.probability}%
                  </span>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>{s.description}</p>
                <p className="text-xs italic" style={{ color: 'var(--muted)', opacity: 0.75 }}>
                  Trigger: {s.trigger}
                </p>
              </div>
            ))}
          </div>
        </Section>
      )}

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {/* Catalysts */}
        {thesis.catalysts.length > 0 && (
          <Section title="Catalysts">
            <ul className="space-y-1">
              {thesis.catalysts.map((c, i) => (
                <li key={i} className="flex gap-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <span style={{ color: 'var(--up)' }}>+</span>
                  {c}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Invalidation */}
        {thesis.invalidation_conditions.length > 0 && (
          <Section title="Invalidation">
            <ul className="space-y-1">
              {thesis.invalidation_conditions.map((c, i) => (
                <li key={i} className="flex gap-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <span style={{ color: 'var(--down)' }}>✕</span>
                  {c}
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>

      {/* Counter-arguments */}
      {thesis.counter_arguments.length > 0 && (
        <Section title="Counter-arguments">
          <div className="space-y-1">
            {thesis.counter_arguments.map(c => (
              <div key={c.id} className="flex gap-3 text-xs" style={{ color: 'var(--muted)' }}>
                <span
                  className="shrink-0 px-1.5 py-0.5 rounded text-xs mono"
                  style={{
                    color: STRENGTH_COLOR[c.strength] ?? 'var(--muted)',
                    border: `1px solid ${STRENGTH_COLOR[c.strength] ?? 'var(--line)'}`,
                    opacity: 0.85,
                  }}
                >
                  {c.strength}
                </span>
                {c.argument}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Footer metadata */}
      <div className="pt-2 border-t flex items-center gap-3 flex-wrap" style={{ borderColor: 'var(--line)' }}>
        <span className="mono text-xs" style={{ color: 'var(--muted)', opacity: 0.6 }}>
          {thesis.model_name}
        </span>
        {thesis.generation_ms && (
          <span className="mono text-xs" style={{ color: 'var(--muted)', opacity: 0.6 }}>
            {thesis.generation_ms}ms
          </span>
        )}
        {thesis.input_tokens && thesis.output_tokens && (
          <span className="mono text-xs" style={{ color: 'var(--muted)', opacity: 0.6 }}>
            {thesis.input_tokens}↑ {thesis.output_tokens}↓ tokens
          </span>
        )}
      </div>
    </div>
  );
}
