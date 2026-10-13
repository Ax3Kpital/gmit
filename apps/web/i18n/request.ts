import { getRequestConfig } from 'next-intl/server';
import { cookies } from 'next/headers';

export type Locale = 'ro' | 'en';
export const LOCALES: Locale[] = ['ro', 'en'];
export const DEFAULT_LOCALE: Locale = 'ro';

export default getRequestConfig(async () => {
  const cookieStore = cookies();
  const raw = cookieStore.get('GMIT_LOCALE')?.value ?? DEFAULT_LOCALE;
  const locale: Locale = LOCALES.includes(raw as Locale) ? (raw as Locale) : DEFAULT_LOCALE;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
