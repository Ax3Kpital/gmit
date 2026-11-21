'use client';

import { useState } from 'react';
import { Panel } from '@/components/ui/Panel';

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

interface Props {
  initialEvents: AlertEvent[];
  initialRules: AlertRule[];
}

const SERIES_OPTIONS = [
  { value: 'DGS10', label: '10Y Treasury Yield' },
  { value: 'DGS2', label: '2Y Treasury Yield' },
  { value: 'T10Y2Y', label: '10Y-2Y Spread' },
  { value: 'DCOILWTICO', label: 'WTI Crude Oil' },
  { value: 'DCOILBRENTEU', label: 'Brent Crude Oil' },
  { value: 'SP500', label: 'S&P 500' },
  { value: 'DEXUSEU', label: 'EUR/USD' },
];

const COT_OPTIONS = [
  { value: '088691', label: 'Gold' },
  { value: '067651', label: 'WTI Crude Oil' },
  { value: '13874A', label: 'S&P 500 E-mini' },
  { value: '099741', label: 'Euro FX' },
  { value: '043602', label: '10-Year T-Note' },
  { value: '023651', label: 'Natural Gas' },
];

export function AlertsClient({ initialEvents, initialRules }: Props) {
  const [events, setEvents] = useState<AlertEvent[]>(initialEvents);
  const [rules, setRules] = useState<AlertRule[]>(initialRules);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '',
    rule_type: 'price_threshold',
    series_id: 'DGS10',
    cftc_code: '088691',
    condition: 'above',
    threshold_value: '',
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleCreateRule(e: React.FormEvent) {
    e.preventDefault();
    if (!form.threshold_value) { setFormError('Enter a threshold value'); return; }
    setSaving(true); setFormError(null);
    try {
      const body = {
        name: form.name || (form.rule_type === 'price_threshold'
          ? `${form.series_id} ${form.condition} ${form.threshold_value}`
          : `${form.cftc_code} COT ${form.condition} ${form.threshold_value}th pct`),
        rule_type: form.rule_type,
        series_id: form.rule_type === 'price_threshold' ? form.series_id : null,
        cftc_code: form.rule_type === 'cot_extreme' ? form.cftc_code : null,
        condition: form.condition,
        threshold_value: parseFloat(form.threshold_value),
      };
      const res = await fetch('/api/alerts/rules', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d?.detail ?? 'Failed'); }
      const rule: AlertRule = await res.json();
      setRules(prev => [rule, ...prev]);
      setShowForm(false);
      setForm({ name: '', rule_type: 'price_threshold', series_id: 'DGS10', cftc_code: '088691', condition: 'above', threshold_value: '' });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteRule(id: string) {
    await fetch(`/api/alerts/rules/${id}`, { method: 'DELETE', credentials: 'include' });
    setRules(prev => prev.filter(r => r.id !== id));
  }

  async function handleAcknowledge(id: string) {
    const res = await fetch(`/api/alerts/events/${id}/acknowledge`, { method: 'PUT', credentials: 'include' });
    if (res.ok) {
      const updated: AlertEvent = await res.json();
      setEvents(prev => prev.map(e => e.id === id ? updated : e));
    }
  }

  const unread = events.filter(e => !e.acknowledged).length;

  return (
    <div className="space-y-5">

      {/* Events */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
            Events {unread > 0 && <span className="ml-2 px-1.5 py-0.5 rounded-full text-xs mono" style={{ background: 'var(--down)', color: '#fff' }}>{unread}</span>}
          </h3>
        </div>
        {events.length === 0 ? (
          <Panel>
            <div className="p-6 text-center text-sm" style={{ color: 'var(--muted)' }}>
              No alerts triggered yet. Create a rule below.
            </div>
          </Panel>
        ) : (
          <div className="space-y-2">
            {events.map(ev => (
              <div
                key={ev.id}
                className="rounded-xl p-4 flex items-start justify-between gap-3"
                style={{
                  background: 'var(--panel)',
                  border: `1px solid ${ev.acknowledged ? 'var(--line)' : 'var(--down)'}`,
                  opacity: ev.acknowledged ? 0.6 : 1,
                }}
              >
                <div className="space-y-1 flex-1 min-w-0">
                  <p className="text-sm leading-snug" style={{ color: 'var(--text)' }}>{ev.message}</p>
                  <p className="text-xs mono" style={{ color: 'var(--muted)' }}>
                    {new Date(ev.triggered_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    {ev.acknowledged && ' · acknowledged'}
                  </p>
                </div>
                {!ev.acknowledged && (
                  <button
                    onClick={() => handleAcknowledge(ev.id)}
                    className="shrink-0 text-xs px-3 py-1 rounded-lg"
                    style={{ background: 'var(--line)', color: 'var(--muted)' }}
                  >
                    Ack
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Rules */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Rules</h3>
          <button
            onClick={() => setShowForm(v => !v)}
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{ background: 'var(--accent)', color: '#fff' }}
          >
            + New rule
          </button>
        </div>

        {showForm && (
          <Panel>
            <form onSubmit={handleCreateRule} className="p-4 space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs mb-1 block" style={{ color: 'var(--muted)' }}>Type</label>
                  <select
                    value={form.rule_type}
                    onChange={e => setForm(p => ({ ...p, rule_type: e.target.value }))}
                    className="w-full rounded-lg px-3 py-2 text-sm"
                    style={{ background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)' }}
                  >
                    <option value="price_threshold">Price threshold (FRED series)</option>
                    <option value="cot_extreme">COT extreme positioning</option>
                  </select>
                </div>

                {form.rule_type === 'price_threshold' ? (
                  <div>
                    <label className="text-xs mb-1 block" style={{ color: 'var(--muted)' }}>Series</label>
                    <select
                      value={form.series_id}
                      onChange={e => setForm(p => ({ ...p, series_id: e.target.value }))}
                      className="w-full rounded-lg px-3 py-2 text-sm"
                      style={{ background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)' }}
                    >
                      {SERIES_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                ) : (
                  <div>
                    <label className="text-xs mb-1 block" style={{ color: 'var(--muted)' }}>Instrument</label>
                    <select
                      value={form.cftc_code}
                      onChange={e => setForm(p => ({ ...p, cftc_code: e.target.value }))}
                      className="w-full rounded-lg px-3 py-2 text-sm"
                      style={{ background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)' }}
                    >
                      {COT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                )}

                <div>
                  <label className="text-xs mb-1 block" style={{ color: 'var(--muted)' }}>Condition</label>
                  <select
                    value={form.condition}
                    onChange={e => setForm(p => ({ ...p, condition: e.target.value }))}
                    className="w-full rounded-lg px-3 py-2 text-sm"
                    style={{ background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)' }}
                  >
                    <option value="above">Above threshold</option>
                    <option value="below">Below threshold</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs mb-1 block" style={{ color: 'var(--muted)' }}>
                    {form.rule_type === 'cot_extreme' ? 'Percentile threshold (0-100)' : 'Threshold value'}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={form.threshold_value}
                    onChange={e => setForm(p => ({ ...p, threshold_value: e.target.value }))}
                    placeholder={form.rule_type === 'cot_extreme' ? 'e.g. 80' : 'e.g. 5.0'}
                    className="w-full rounded-lg px-3 py-2 text-sm"
                    style={{ background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)' }}
                  />
                </div>
              </div>

              {formError && <p className="text-xs" style={{ color: 'var(--down)' }}>{formError}</p>}

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="text-xs px-3 py-1.5 rounded-lg"
                  style={{ background: 'var(--line)', color: 'var(--muted)' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="text-xs px-4 py-1.5 rounded-lg"
                  style={{ background: 'var(--accent)', color: '#fff', opacity: saving ? 0.6 : 1 }}
                >
                  {saving ? 'Saving...' : 'Create rule'}
                </button>
              </div>
            </form>
          </Panel>
        )}

        {rules.length === 0 && !showForm && (
          <Panel>
            <div className="p-6 text-center text-sm" style={{ color: 'var(--muted)' }}>
              No alert rules configured.
            </div>
          </Panel>
        )}

        {rules.map(rule => (
          <div
            key={rule.id}
            className="rounded-xl p-4 flex items-center justify-between gap-3"
            style={{ background: 'var(--panel)', border: '1px solid var(--line)' }}
          >
            <div className="space-y-0.5">
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{rule.name}</p>
              <p className="text-xs mono" style={{ color: 'var(--muted)' }}>
                {rule.rule_type === 'price_threshold'
                  ? `${rule.series_id} ${rule.condition} ${rule.threshold_value}`
                  : `COT ${rule.cftc_code} percentile ${rule.condition} ${rule.threshold_value}%`
                }
              </p>
            </div>
            <button
              onClick={() => handleDeleteRule(rule.id)}
              className="text-xs px-2 py-1 rounded"
              style={{ color: 'var(--down)', background: 'var(--line)' }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
