import { Link, useParams } from 'react-router-dom';
import { LifecycleTimeline } from '../components/dashboard/LifecycleTimeline';
import { useAsset } from '../hooks/useAsset';
import { formatCompactCurrency, formatCurrency, formatPercent, formatRisk } from '../lib/formatters';

export function AssetDetailPage() {
  const { assetId = 'AST-1001' } = useParams();
  const { data, isLoading, error, retry } = useAsset(assetId);

  if (isLoading) {
    return <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-12 text-center text-[15px] text-[var(--color-deep-ink)]">Loading asset data…</div>;
  }

  if (error || !data) {
    return (
      <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-10 text-center">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--color-cool-ash)]">Unable to load asset data</div>
        <p className="mt-4 text-[16px] leading-7 text-[var(--color-deep-ink)]">The backend may be unavailable.</p>
        <button type="button" onClick={() => void retry()} className="mt-6 rounded-full bg-[var(--color-deep-ink)] px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-pure-white)]">
          Retry
        </button>
      </div>
    );
  }

  const { asset, risk, financing, aiDecision, sourceEvidence, financingHistory, alerts, auditHistory } = data;

  return (
    <div className="space-y-8">
      <header className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6 sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Asset</div>
            <h1 className="mt-3 text-[34px] font-bold tracking-[-0.08em] text-[var(--color-deep-ink)] sm:text-[52px]">{asset.name}</h1>
            <div className="mt-3 text-[12px] uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">{asset.product}</div>
          </div>

          <div className="flex items-center gap-3">
            <div className="rounded-full border border-[var(--color-pebble)] px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-deep-ink)]">{asset.owner}</div>
            <div className="rounded-full border border-[var(--color-deep-ink)] bg-[var(--color-deep-ink)] px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-pure-white)]">{asset.currentStageLabel}</div>
          </div>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Current value</div>
          <div className="mt-4 text-[32px] font-bold tracking-[-0.07em] text-[var(--color-deep-ink)]">{formatCompactCurrency(asset.currentValue)}</div>
        </div>
        <div className="border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Physical</div>
          <div className="mt-4 text-[24px] font-semibold tracking-[-0.05em] text-[var(--color-deep-ink)]">{asset.physicalState}</div>
        </div>
        <div className="border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Financial</div>
          <div className="mt-4 text-[24px] font-semibold tracking-[-0.05em] text-[var(--color-deep-ink)]">{asset.financialState}</div>
        </div>
      </section>

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-5 sm:p-7">
        <div className="mb-6 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-cool-ash)]">Lifecycle</div>
        <LifecycleTimeline asset={asset} />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Financing</div>
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Recommended</div>
              <div className="mt-2 text-[24px] font-bold tracking-[-0.05em] text-[var(--color-deep-ink)]">{formatCompactCurrency(financing.recommendedAmount)}</div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Instrument</div>
              <div className="mt-2 text-[24px] font-bold tracking-[-0.05em] text-[var(--color-deep-ink)]">{financing.recommendedInstrument.replace(/_/g, ' ')}</div>
            </div>
          </div>
          <div className="mt-6 border-t border-[var(--color-pebble)] pt-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Decision factors</div>
            <ul className="mt-3 space-y-2 text-[15px] leading-6 text-[var(--color-deep-ink)]">
              {financing.decisionFactors.map((factor) => (
                <li key={factor}>• {factor}</li>
              ))}
            </ul>
          </div>
          <Link to={`/assets/${asset.id}/financing`} className="mt-6 inline-flex rounded-full border border-[var(--color-deep-ink)] bg-[var(--color-deep-ink)] px-5 py-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-pure-white)]">
            Open financing
          </Link>
        </div>

        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Risk</div>
          <div className="text-[42px] font-bold tracking-[-0.08em] text-[var(--color-deep-ink)]">{formatRisk(risk.score)}</div>
          <div className="mt-2 text-[12px] uppercase tracking-[0.22em] text-[var(--color-cool-ash)]">{risk.level}</div>
          <div className="mt-6 space-y-3">
            {risk.components.map((item) => (
              <div key={item.label} className="flex items-center justify-between border-b border-[var(--color-pebble)] pb-2">
                <span className="text-[14px] text-[var(--color-deep-ink)]">{item.label}</span>
                <span className="text-[14px] font-semibold text-[var(--color-deep-ink)]">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">AI decision</div>
          <div className="text-[18px] font-semibold tracking-[-0.04em] text-[var(--color-deep-ink)]">{aiDecision.status}</div>
          <p className="mt-4 text-[16px] leading-7 text-[var(--color-deep-ink)]">{aiDecision.summary}</p>
          <div className="mt-6 text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Decision factors</div>
          <ul className="mt-3 space-y-2 text-[15px] leading-6 text-[var(--color-deep-ink)]">
            {aiDecision.factors.map((factor) => (
              <li key={factor}>• {factor}</li>
            ))}
          </ul>
          <div className="mt-6 text-[11px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Confidence</div>
          <div className="mt-2 text-[28px] font-bold tracking-[-0.06em] text-[var(--color-deep-ink)]">{formatPercent(aiDecision.confidence)}</div>
        </div>

        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Source evidence</div>
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-pebble)] pb-2">
              <span className="text-[12px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Canonical value</span>
              <span className="text-[18px] font-semibold tracking-[-0.04em] text-[var(--color-deep-ink)]">{sourceEvidence.canonicalValue}</span>
            </div>
            <div className="flex items-center justify-between border-b border-[var(--color-pebble)] pb-2">
              <span className="text-[12px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Confidence</span>
              <span className="text-[18px] font-semibold tracking-[-0.04em] text-[var(--color-deep-ink)]">{sourceEvidence.confidence}%</span>
            </div>
            <div>
              <div className="text-[12px] uppercase tracking-[0.18em] text-[var(--color-cool-ash)]">Resolution reason</div>
              <p className="mt-2 text-[15px] leading-6 text-[var(--color-deep-ink)]">{sourceEvidence.resolutionReason}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Financing history</div>
          <div className="space-y-3">
            {financingHistory.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between border-b border-[var(--color-pebble)] pb-3">
                <div>
                  <div className="text-[15px] font-semibold text-[var(--color-deep-ink)]">{entry.instrument}</div>
                  <div className="text-[11px] uppercase tracking-[0.16em] text-[var(--color-cool-ash)]">{entry.date}</div>
                </div>
                <div className="text-right">
                  <div className="text-[15px] font-semibold text-[var(--color-deep-ink)]">{formatCurrency(entry.amount)}</div>
                  <div className="text-[11px] uppercase tracking-[0.16em] text-[var(--color-cool-ash)]">{entry.status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
          <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Alerts</div>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-cool-ash)]">{alert.severity}</div>
                <div className="mt-2 text-[17px] font-semibold tracking-[-0.04em] text-[var(--color-deep-ink)]">{alert.title}</div>
                <p className="mt-2 text-[14px] leading-6 text-[var(--color-deep-ink)]">{alert.message}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-none border border-[var(--color-pebble)] bg-[var(--color-pure-white)] p-6">
        <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-cool-ash)]">Audit history</div>
        <div className="space-y-3">
          {auditHistory.map((entry) => (
            <div key={entry.id} className="flex items-center justify-between border-b border-[var(--color-pebble)] pb-3 text-[14px] text-[var(--color-deep-ink)]">
              <span>{entry.summary}</span>
              <span className="text-[11px] uppercase tracking-[0.16em] text-[var(--color-cool-ash)]">{new Date(entry.createdAt).toLocaleDateString()}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
