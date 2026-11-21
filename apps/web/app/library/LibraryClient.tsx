'use client';

import { useState } from 'react';
import { CreateThesisForm } from '@/components/research/CreateThesisForm';
import { ThesisCard, type ThesisFull } from '@/components/research/ThesisCard';
import { Panel } from '@/components/ui/Panel';

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

interface Props {
  initialTheses: ThesisSummary[];
  labels: {
    topicPlaceholder: string;
    generate: string;
    generating: string;
    errorEmpty: string;
    errorFailed: string;
    noTheses: string;
    demoNotice: string;
  };
}

export function LibraryClient({ initialTheses, labels }: Props) {
  // Full theses created in this session (with all details)
  const [sessionTheses, setSessionTheses] = useState<ThesisFull[]>([]);

  // Summary list from server (may not have full details)
  const [summaries, setSummaries] = useState<ThesisSummary[]>(initialTheses);

  function handleCreated(thesis: ThesisFull) {
    setSessionTheses(prev => [thesis, ...prev]);
    setSummaries(prev => [
      {
        id: thesis.id,
        topic: thesis.topic,
        claim: thesis.claim,
        confidence: thesis.confidence,
        time_horizon: thesis.time_horizon,
        provider: thesis.provider,
        is_demo: thesis.is_demo,
        created_at: thesis.created_at,
      },
      ...prev.filter(s => s.id !== thesis.id),
    ]);
  }

  const sessionIds = new Set(sessionTheses.map(t => t.id));

  return (
    <div className="space-y-5">

      {/* Create new thesis */}
      <Panel>
        <div className="p-4 space-y-4">
          <CreateThesisForm
            onCreated={handleCreated}
            labels={{
              topicPlaceholder: labels.topicPlaceholder,
              generate: labels.generate,
              generating: labels.generating,
              errorEmpty: labels.errorEmpty,
              errorFailed: labels.errorFailed,
            }}
          />
          {summaries.some(s => s.is_demo) && (
            <p className="text-xs" style={{ color: 'var(--warn)', opacity: 0.75 }}>
              {labels.demoNotice}
            </p>
          )}
        </div>
      </Panel>

      {/* Full cards for theses created this session */}
      {sessionTheses.map(thesis => (
        <ThesisCard key={thesis.id} thesis={thesis} expanded />
      ))}

      {/* Summary cards for older theses (not in session) */}
      {summaries
        .filter(s => !sessionIds.has(s.id))
        .map(s => (
          <div
            key={s.id}
            className="rounded-xl p-4"
            style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1 flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className="mono text-xs px-2 py-0.5 rounded-full"
                    style={{ background: 'var(--line)', color: 'var(--muted)' }}
                  >
                    {s.time_horizon}
                  </span>
                  <span
                    className="mono text-xs px-2 py-0.5 rounded-full"
                    style={{
                      color: s.confidence >= 65 ? 'var(--up)' : s.confidence >= 40 ? 'var(--warn)' : 'var(--down)',
                      border: `1px solid ${s.confidence >= 65 ? 'var(--up)' : s.confidence >= 40 ? 'var(--warn)' : 'var(--down)'}`,
                    }}
                  >
                    {s.confidence}%
                  </span>
                  {s.is_demo && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(230,184,76,0.15)', color: 'var(--warn)', border: '1px solid var(--warn)' }}
                    >
                      DEMO
                    </span>
                  )}
                  <span className="text-xs truncate" style={{ color: 'var(--muted)' }}>
                    {s.topic}
                  </span>
                </div>
                <p className="text-sm leading-snug" style={{ color: 'var(--text)' }}>
                  {s.claim}
                </p>
              </div>
              <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
                {new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            </div>
          </div>
        ))}

      {summaries.length === 0 && sessionTheses.length === 0 && (
        <div
          className="rounded-xl p-10 text-center"
          style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
        >
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {labels.noTheses}
          </p>
        </div>
      )}
    </div>
  );
}
