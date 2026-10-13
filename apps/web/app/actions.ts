'use server';

import { cookies } from 'next/headers';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { LOCALES, type Locale } from '@/i18n/request';

const API_URL = process.env.API_URL ?? 'http://localhost:8000';

export async function setLocale(locale: string) {
  const safe: Locale = LOCALES.includes(locale as Locale) ? (locale as Locale) : 'ro';
  cookies().set('GMIT_LOCALE', safe, {
    path: '/',
    maxAge: 365 * 24 * 60 * 60,
    sameSite: 'lax',
    httpOnly: false,
  });
  revalidatePath('/', 'layout');
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    cache: 'no-store',
  });

  if (!res.ok) {
    return { ok: false, error: 'invalidCredentials' };
  }

  const data = await res.json();
  const sessionToken = res.headers.get('set-cookie');

  // Forward the session cookie from the backend to the browser
  if (sessionToken) {
    const match = sessionToken.match(/gmit_session=([^;]+)/);
    if (match) {
      cookies().set('gmit_session', match[1], {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7,
      });
    }
  }

  return { ok: true, user: data.user };
}

export async function logout() {
  const sessionToken = cookies().get('gmit_session')?.value;
  if (sessionToken) {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: { Cookie: `gmit_session=${sessionToken}` },
      cache: 'no-store',
    }).catch(() => {});
  }
  cookies().delete('gmit_session');
  redirect('/login');
}
