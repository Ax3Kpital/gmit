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
