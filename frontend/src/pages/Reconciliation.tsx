import { useParams } from 'react-router-dom';
import { useReconciliation } from '../hooks/useReconciliation';

export function ReconciliationPage() {
  const { assetId = 'AST-1001' } = useParams();
  const { data, isLoading, error, retry } = useReconciliation(assetId);

  if (isLoading) {
    return <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-12 text-center text-[15px] text-[var(--color-deep-ink)]">Loading reconciliation data…</div>;
  }

  if (error || !data) {
    return (
      <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-10 text-center">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--color-cool-ash)]">Unable to load reconciliation layer</div>
        <p className="mt-4 text-[16px] leading-7 text-[var(--color-deep-ink)]">The backend may be unavailable.</p>
        <button type="button" onClick={() => void retry()} className="mt-6 rounded-full bg-[var(--color-deep-ink)] px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-pure-white)]">
          Retry
        </button>
      </div>
    );
  }

  const sources = Array.from(new Set(data.sources.flatMap((record) => Object.keys(record.values))));

  return (
    <div className="space-y-8">
      <header className="border-b border-[var(--color-pebble)] pb-6">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Source evidence</div>
        <h1 className="mt-3 text-[34px] font-bold tracking-[-0.08em] text-[var(--color-deep-ink)] sm:text-[52px]">Reconciliation center</h1>
      </header>

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5 sm:p-6">
        <div className="overflow-x-auto">
          <table className="min-w-[640px] w-full border-collapse text-left text-[14px] text-[var(--color-deep-ink)]">
            <thead>
              <tr className="border-b border-[var(--color-pebble)]">
                <th className="pb-3 pr-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Field</th>
                {sources.map((source) => (
                  <th key={source} className="pb-3 pr-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">{source}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.sources.map((record, index) => (
                <tr key={`${record.field}-${index}`} className="border-b border-[var(--color-pebble)]">
                  <td className="py-3 pr-6 font-medium">{record.field.replace(/_/g, ' ')}</td>
                  {sources.map((source) => <td key={source} className="py-3 pr-6">{record.values[source] || '—'}</td>)}
                </tr>
              ))}
              {!data.sources.length && <tr><td className="py-6 text-[var(--color-cool-ash)]" colSpan={Math.max(1, sources.length + 1)}>No source conflicts detected.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-deep-ink)] p-6 text-[var(--color-pure-white)] sm:p-8">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[rgba(255,255,255,0.7)]">{data.conflictDetected ? 'Conflict detected' : 'Sources reconciled'}</div>
        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.68)]">Canonical value</div>
            <div className="mt-3 text-[38px] font-bold tracking-[-0.08em]">{data.canonicalValue}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.68)]">Confidence</div>
            <div className="mt-3 text-[38px] font-bold tracking-[-0.08em]">{data.confidence}%</div>
          </div>
        </div>
        <div className="mt-8 border-t border-[rgba(255,255,255,0.2)] pt-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.68)]">Resolution reason</div>
          <p className="mt-3 max-w-2xl text-[16px] leading-7 text-[rgba(255,255,255,0.8)]">{data.resolutionReason}</p>
        </div>
      </section>
    </div>
  );
}
