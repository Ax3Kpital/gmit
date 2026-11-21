'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** Re-runs the page's server fetches every `seconds` so prices never sit on screen for hours. */
export function AutoRefresh({ seconds = 60 }: { seconds?: number }) {
  const router = useRouter();
  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') router.refresh();
    }, seconds * 1000);
    return () => clearInterval(id);
  }, [router, seconds]);
  return null;
}
