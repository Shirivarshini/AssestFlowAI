import { useParams } from 'react-router-dom';
import { DecisionPanel } from '../components/financing/DecisionPanel';
import { useFinancing } from '../hooks/useFinancing';

export function FinancingPage() {
  const { assetId = 'AST-1001' } = useParams();
  const { data, isLoading, error, retry } = useFinancing(assetId);

  if (isLoading) {
    return <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-12 text-center text-[15px] text-[var(--color-deep-ink)]">Loading financing decision…</div>;
  }

  if (error || !data) {
    return (
      <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-10 text-center">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--color-cool-ash)]">Unable to load financing data</div>
        <p className="mt-4 text-[16px] leading-7 text-[var(--color-deep-ink)]">The backend may be unavailable.</p>
        <button type="button" onClick={() => void retry()} className="mt-6 rounded-full bg-[var(--color-deep-ink)] px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-pure-white)]">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="border-b border-[var(--color-pebble)] pb-6">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Asset financing</div>
        <h1 className="mt-3 text-[34px] font-bold tracking-[-0.08em] text-[var(--color-deep-ink)] sm:text-[52px]">{assetId}</h1>
      </header>

      <DecisionPanel financing={data} />

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-cool-ash)]">Transition pattern</div>
        <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          {['PURCHASE ORDER', 'PROCUREMENT', 'INVENTORY', 'IN-TRANSIT', 'WAREHOUSE', 'INVOICE', 'RECEIVABLE', 'SETTLED'].map((step, index, array) => (
            <div key={step} className="flex items-center gap-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-deep-ink)]">
              <span className={index < 7 ? 'text-[var(--color-deep-ink)]' : 'text-[var(--color-cool-ash)]'}>{step}</span>
              {index < array.length - 1 && <span className="text-[var(--color-cool-ash)]">↓</span>}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
