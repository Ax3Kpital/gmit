'use client';

import { useState } from 'react';
import type { ThesisFull } from './ThesisCard';

interface Props {
  onCreated: (thesis: ThesisFull) => void;
  labels: {
    topicPlaceholder: string;
    generate: string;
    generating: string;
    errorEmpty: string;
    errorFailed: string;
  };
}

export function CreateThesisForm({ onCreated, labels }: Props) {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = topic.trim();
    if (!trimmed) {
      setError(labels.errorEmpty);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/research/thesis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ topic: trimmed }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? labels.errorFailed);
      }
      const thesis: ThesisFull = await res.json();
      setTopic('');
      onCreated(thesis);
    } catch (err) {
      setError(err instanceof Error ? err.message : labels.errorFailed);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex gap-3">
        <input
          type="text"
          value={topic}
          onChange={e => setTopic(e.target.value)}
          disabled={loading}
          placeholder={labels.topicPlaceholder}
          maxLength={500}
          className="flex-1 rounded-lg px-4 py-2.5 text-sm outline-none"
          style={{
            background: 'var(--input, var(--bg))',
            border: '1px solid var(--line)',
            color: 'var(--text)',
          }}
        />
        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="px-5 py-2.5 rounded-lg text-sm font-medium transition-opacity"
          style={{
            background: 'var(--accent)',
            color: '#fff',
            opacity: loading || !topic.trim() ? 0.5 : 1,
            cursor: loading || !topic.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              {labels.generating}
            </span>
          ) : (
            labels.generate
          )}
        </button>
      </div>
      {error && (
        <p className="text-xs" style={{ color: 'var(--down)' }}>
          {error}
        </p>
      )}
    </form>
  );
}
