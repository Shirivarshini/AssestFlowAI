import { useEffect, useState } from 'react';

export function use3DEnabled() {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setEnabled(!media.matches && typeof window.WebGLRenderingContext !== 'undefined');
    update(); media.addEventListener?.('change', update);
    return () => media.removeEventListener?.('change', update);
  }, []);
  return enabled;
}
