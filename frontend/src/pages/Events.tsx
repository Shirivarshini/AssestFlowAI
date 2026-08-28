import { useMemo } from 'react';
import { useEvents } from '../hooks/useEvents';
import { formatCurrency } from '../lib/formatters';

const supportedEvents = [
  'PRODUCTION_DELAY',
  'SHIPMENT_DELAY',
  'INVENTORY_DETERIORATION',
  'WAREHOUSE_EXCEPTION',
  'DELIVERY_CONFIRMED',
  'BUYER_RISK_CHANGED',
  'RECEIVABLE_DELAY',
  'INVOICE_VERIFIED',
  'DATA_CONFLICT',
];

export function EventsPage() {
  const { data, assetId, isLoading, error, retry, fireEvent, lastTriggered } = useEvents();

  const eventButtons = useMemo(() => supportedEvents, []);

  if (isLoading) {
    return <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-12 text-center text-[15px] text-[var(--color-deep-ink)]">Loading event monitor…</div>;
  }

  if (error) {
    return (
      <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-10 text-center">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--color-cool-ash)]">Unable to load event monitor</div>
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
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Event monitor</div>
        <h1 className="mt-3 text-[34px] font-bold tracking-[-0.08em] text-[var(--color-deep-ink)] sm:text-[52px]">Material event simulator</h1>
      </header>

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Trigger a material event</div>
        <div className="mt-5 flex flex-wrap gap-3">
          {eventButtons.map((eventType) => (
            <button
              key={eventType}
              type="button"
              onClick={() => void fireEvent(assetId, eventType as never)}
              className="rounded-full border border-[var(--color-deep-ink)] px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-deep-ink)] transition hover:bg-[var(--color-deep-ink)] hover:text-[var(--color-pure-white)]"
            >
              {eventType.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </section>

      {lastTriggered && (
        <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-deep-ink)] p-6 text-[var(--color-pure-white)] sm:p-8">
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[rgba(255,255,255,0.7)]">Before / after</div>
          <h2 className="mt-3 text-[28px] font-bold tracking-[-0.06em]">{lastTriggered.type.replace(/_/g, ' ')} detected</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="border border-[rgba(255,255,255,0.2)] p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.7)]">Before</div>
              <div className="mt-4 text-[15px] text-[rgba(255,255,255,0.82)]">Risk {lastTriggered.before.risk}</div>
              <div className="mt-2 text-[15px] text-[rgba(255,255,255,0.82)]">Financing {formatCurrency(lastTriggered.before.financing)}</div>
            </div>
            <div className="border border-[rgba(255,255,255,0.2)] p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.7)]">After</div>
              <div className="mt-4 text-[15px] text-[rgba(255,255,255,0.82)]">Risk {lastTriggered.after.risk}</div>
              <div className="mt-2 text-[15px] text-[rgba(255,255,255,0.82)]">Financing {formatCurrency(lastTriggered.after.financing)}</div>
            </div>
          </div>
          <div className="mt-8 text-[11px] uppercase tracking-[0.18em] text-[rgba(255,255,255,0.7)]">Resulting action</div>
          <div className="mt-2 text-[28px] font-bold tracking-[-0.06em]">{lastTriggered.action}</div>
        </section>
      )}

      <section className="grid gap-4">
        {data.map((event) => (
          <article key={event.id} className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="text-[9px] font-semibold uppercase tracking-[0.2em] text-[var(--color-cool-ash)]">{event.type}</div>
                <div className="mt-2 text-[24px] font-bold tracking-[-0.05em] text-[var(--color-deep-ink)]">{event.assetId}</div>
              </div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">{new Date(event.timestamp).toLocaleString()}</div>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Before</div>
                <div className="mt-2 text-[15px] leading-6 text-[var(--color-deep-ink)]">Risk {event.before.risk}</div>
                <div className="text-[15px] leading-6 text-[var(--color-deep-ink)]">Financing {formatCurrency(event.before.financing)}</div>
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">After</div>
                <div className="mt-2 text-[15px] leading-6 text-[var(--color-deep-ink)]">Risk {event.after.risk}</div>
                <div className="text-[15px] leading-6 text-[var(--color-deep-ink)]">Financing {formatCurrency(event.after.financing)}</div>
              </div>
            </div>
            <div className="mt-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Action</div>
            <div className="mt-2 text-[18px] font-semibold tracking-[-0.04em] text-[var(--color-deep-ink)]">{event.action}</div>
          </article>
        ))}
      </section>
    </div>
  );
}
