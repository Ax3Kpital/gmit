/** Research output is only shown as current while it is based on recent data. */
export const THESIS_MAX_AGE_DAYS = 3;

export function ageInDays(iso: string, now: Date = new Date()): number {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return Infinity;
  return Math.floor((now.getTime() - t) / 86_400_000);
}

export function isFresh(iso: string, maxDays: number = THESIS_MAX_AGE_DAYS): boolean {
  return ageInDays(iso) <= maxDays;
}
