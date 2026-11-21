import { cookies } from 'next/headers';

const SERVER_API = process.env.API_URL ?? 'http://localhost:8001';

export async function serverFetch<T>(path: string): Promise<T | null> {
  const cookieStore = cookies();
  const session = cookieStore.get('gmit_session');

  try {
    const res = await fetch(`${SERVER_API}${path}`, {
      headers: session ? { Cookie: `gmit_session=${session.value}` } : {},
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}
