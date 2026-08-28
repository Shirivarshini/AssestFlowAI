import { lazy, Suspense } from 'react';
import type { Asset } from '../../types/api';
import { use3DEnabled } from '../../hooks/use3DEnabled';

const LifecycleRail3D = lazy(() => import('../three/LifecycleRail3D'));

interface LifecycleTimelineProps {
  asset: Asset;
  shockwaveKey?: number;
}

const stageOrder = [
  'PURCHASE_ORDER',
  'RAW_MATERIAL',
  'PRODUCTION',
  'FINISHED_GOODS',
  'SHIPMENT',
  'WAREHOUSE',
  'DELIVERY',
  'INVOICE',
  'RECEIVABLE',
  'CASH_REALISATION',
];

export function LifecycleTimeline({ asset, shockwaveKey = 0 }: LifecycleTimelineProps) {
  const enabled3D = use3DEnabled();
  if (enabled3D) return <Suspense fallback={<StaticTimeline asset={asset} />}><LifecycleRail3D asset={asset} shockwaveKey={shockwaveKey} /></Suspense>;
  return <StaticTimeline asset={asset} />;
}

function StaticTimeline({ asset }: { asset: Asset }) {
  const currentIndex = stageOrder.indexOf(asset.currentStage);

  return (
    <div className="overflow-x-auto pb-2">
      <div className="flex min-w-[760px] items-start gap-4">
        {asset.timeline.map((step, index) => {
          const isCurrent = step.stage === asset.currentStage;
          const isComplete = index < currentIndex;
          const isUpcoming = index > currentIndex;

          return (
            <div key={step.stage} className="flex min-w-[120px] flex-1 flex-col items-center text-center">
              <div className="mb-3 flex w-full items-center justify-center">
                <div className={`h-px flex-1 ${isComplete || isCurrent ? 'bg-[var(--color-deep-ink)]' : 'bg-[var(--color-pebble)]'}`} />
                <div
                  className={`relative flex h-5 w-5 items-center justify-center border ${
                    isCurrent
                      ? 'border-[var(--color-deep-ink)] bg-[var(--color-deep-ink)]'
                      : isComplete
                        ? 'border-[var(--color-deep-ink)] bg-[var(--color-pure-white)]'
                        : 'border-[var(--color-pebble)] bg-[var(--color-pure-white)]'
                  }`}
                >
                  {isCurrent && <span className="h-2 w-2 rounded-full bg-[var(--color-pure-white)]" />}
                  {isComplete && !isCurrent && <span className="h-2 w-2 rounded-full bg-[var(--color-deep-ink)]" />}
                </div>
                <div className={`h-px flex-1 ${isComplete ? 'bg-[var(--color-deep-ink)]' : 'bg-[var(--color-pebble)]'}`} />
              </div>

              <div className={`rounded-full border px-3 py-1 text-[9px] font-semibold uppercase tracking-[0.22em] ${isCurrent ? 'border-[var(--color-deep-ink)] bg-[var(--color-deep-ink)] text-[var(--color-pure-white)]' : isComplete ? 'border-[var(--color-pebble)] bg-[var(--color-pure-white)] text-[var(--color-deep-ink)]' : 'border-[var(--color-pebble)] bg-[var(--color-pure-white)] text-[var(--color-cool-ash)]'}`}>
                {step.label}
              </div>

              <div className={`mt-3 text-[9px] uppercase tracking-[0.18em] ${isUpcoming ? 'text-[var(--color-cool-ash)]' : 'text-[var(--color-deep-ink)]'}`}>
                {isCurrent ? 'Current' : isComplete ? 'Completed' : 'Queued'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
