export type DataStatus =
  | 'REALTIME'
  | 'DELAYED'
  | 'END_OF_DAY'
  | 'PERIODIC_OFFICIAL_RELEASE'
  | 'INDICATIVE'
  | 'STALE'
  | 'UNAVAILABLE'
  | 'UNKNOWN';

export interface Provider {
  code: string;
  name: string;
  description: string;
  terms: string;
  phase: number;
  configured: boolean;
  status: 'configured' | 'unconfigured' | 'ok' | 'degraded' | 'down' | 'unknown';
  active_phase: boolean;
}

export interface User {
  id: string;
  email: string;
}

export interface MacroObservationPoint {
  date: string;
  value: number | null;
}

export interface MacroSeriesResponse {
  series_id: string;
  title: string;
  provider: string;
  source_url: string;
  units: string;
  data_status: DataStatus;
  last_fetched_at: string | null;
  latest: {
    date: string;
    value: number | null;
    retrieved_at: string;
    provider?: string;
    age?: string;
  } | null;
  history: MacroObservationPoint[];
}
