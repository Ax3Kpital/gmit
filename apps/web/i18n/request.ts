import { getRequestConfig } from 'next-intl/server';

/** GMIT is English-only. next-intl is kept as the message catalogue (messages/en.json). */
export const LOCALE = 'en';

export default getRequestConfig(async () => ({
  locale: LOCALE,
  messages: (await import('../messages/en.json')).default,
}));
