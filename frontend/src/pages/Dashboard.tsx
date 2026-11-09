import { lazy, Suspense, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LifecycleTimeline } from '../components/dashboard/LifecycleTimeline';
import { WorkflowHero } from '../components/dashboard/WorkflowHero';
import { useDashboard } from '../hooks/useDashboard';
import { use3DEnabled } from '../hooks/use3DEnabled';
import { formatCompactCurrency, formatCurrency, formatPercent } from '../lib/formatters';

const AssetNetworkGraph = lazy(() => import('../components/three/AssetNetworkGraph'));
const RiskRibbon = lazy(() => import('../components/three/RiskRibbon'));

function State({ message, retry }: { message: string; retry?: () => void }) { return <div className="panel-dark p-10 text-center"><div className="mono text-[var(--color-signal-orange)]">Console notice</div><p className="mt-4 text-[var(--color-pale-stone)]">{message}</p>{retry && <button onClick={retry} className="control mono mt-6">Retry</button>}</div>; }
const Spark = ({ green = false }: { green?: boolean }) => <svg className="metric-spark mt-5 h-9 w-full" viewBox="0 0 180 36" preserveAspectRatio="none" aria-hidden="true"><path d="M0 27 L22 25 L41 28 L62 16 L83 20 L105 9 L127 15 L149 7 L180 10" fill="none" stroke={green ? 'var(--color-metric-green)' : 'var(--color-signal-orange)'} strokeWidth="1.5" pathLength="1" /></svg>;

export function DashboardPage() {
  const { data, isLoading, error, retry } = useDashboard();
  const enabled3D = use3DEnabled(); const navigate = useNavigate();
  const [activeMetric, setActiveMetric] = useState<number | null>(null);
  if (isLoading) return <div className="console-content"><State message="Synchronising asset network…" /></div>;
  if (error || !data) return <div className="console-content"><State message={error ?? 'Dashboard unavailable.'} retry={() => void retry()} /></div>;
  const { primaryAsset: asset } = data;
  const metrics = [['Tracked assets', String(data.assetCount), true], ['Total exposure', formatCompactCurrency(data.totalExposure), true], ['Open opportunities', String(data.financingOpportunities), true], ['Risk alerts', String(data.riskAlerts), false]] as const;
  return <>
    <WorkflowHero asset={asset} />
    <div className="console-content space-y-20">
      <section aria-labelledby="portfolio-heading">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mono metric-orange">01 / Network intelligence</p>
            <h2 id="portfolio-heading" className="section-title mt-3">Portfolio overview</h2>
          </div>
          <Link to="/simulator" className="control mono">Simulate event ↗</Link>
        </div>
        <div className="panel grid gap-px overflow-hidden bg-[var(--color-ash-stroke)] sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map(([label, value, green], index) => (
            <motion.div
              key={label}
              tabIndex={index === 0 || index === 3 ? 0 : undefined}
              onHoverStart={() => setActiveMetric(index)}
              onHoverEnd={() => setActiveMetric(null)}
              onFocus={() => setActiveMetric(index)}
              onBlur={() => setActiveMetric(null)}
              className="portfolio-metric relative min-h-[154px] overflow-hidden p-5"
            >
              <div className="mono text-[var(--color-pale-stone)]">{label}</div>
              <div className="mt-5 text-4xl tracking-[-.04em]">{value}</div>
              <Spark green={green} />
              {enabled3D && activeMetric === index && index === 0 && <Suspense fallback={null}><AssetNetworkGraph onAssetClick={() => navigate(`/assets/${asset.id}`)} /></Suspense>}
              {enabled3D && activeMetric === index && index === 3 && <Suspense fallback={null}><RiskRibbon /></Suspense>}
            </motion.div>
          ))}
        </div>
      </section>

    <section id="lifecycle-telemetry"><div className="mb-8 flex flex-wrap items-end justify-between gap-4"><div><div className="mono metric-orange">Primary asset / {asset.id}</div><h2 className="section-title mt-4">Lifecycle telemetry</h2></div><Link to={`/assets/${asset.id}`} className="control mono">Open record ↗</Link></div><div className="panel-dark p-5 sm:p-7"><div className="mb-8 flex flex-wrap items-center justify-between gap-4"><div><div className="mono text-[var(--color-warm-granite)]">{asset.product}</div><div className="mt-3 text-2xl tracking-[-.025em]">{asset.currentStageLabel}</div></div><span className="mono flex items-center gap-2 text-[var(--color-metric-green)]"><i className="h-1.5 w-1.5 rounded-full bg-[var(--color-metric-green)]" /> State verified</span></div><LifecycleTimeline asset={asset} /><div className="mt-8 grid border-t border-[var(--color-ash-stroke)] sm:grid-cols-2 lg:grid-cols-5">{[['Current value', formatCompactCurrency(asset.currentValue)], ['Exposure', formatCompactCurrency(asset.existingExposure)], ['Financing need', formatCompactCurrency(asset.financingNeed)], ['Risk score', `${asset.riskScore}/100`], ['Confidence', formatPercent(asset.confidence)]].map(([label, value]) => <div key={label} className="border-b border-[var(--color-ash-stroke)] p-5 lg:border-b-0 lg:border-r last:border-r-0"><div className="mono text-[var(--color-warm-granite)]">{label}</div><div className="mt-4 text-2xl tracking-[-.025em]">{value}</div></div>)}</div></div></section>

    <section className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]"><div className="panel-light grain p-7 sm:p-10"><div className="mono flex items-center gap-2"><i className="signal" /> Financing dispatch</div><h2 className="section-title mt-8 max-w-xl">Value remains eligible for in-transit financing.</h2><p className="mt-6 max-w-xl text-base leading-6 text-[#4d4947]">Physical state is verified, exposure remains within policy, and the current lifecycle milestone supports continued funding.</p><Link to={`/assets/${asset.id}/financing`} className="mt-9 inline-flex min-h-10 items-center rounded-[3px] bg-[var(--color-obsidian-canvas)] px-4 mono text-[var(--color-bone)]">Review decision →</Link></div><div className="panel p-7"><div className="mono text-[var(--color-pale-stone)]">Exposure register</div><div className="mt-8 space-y-5">{[['Asset value', formatCurrency(asset.currentValue)], ['Existing exposure', formatCurrency(asset.existingExposure)], ['Available need', formatCurrency(asset.financingNeed)], ['Risk class', asset.riskLevel]].map(([label, value]) => <div key={label} className="flex items-end justify-between gap-4 border-b border-[var(--color-ash-stroke)] pb-4"><span className="mono text-[var(--color-warm-granite)]">{label}</span><span className="text-xl tracking-[-.025em]">{value}</span></div>)}</div></div></section>
    <section><div className="mb-7 flex items-center justify-between"><div className="mono text-[var(--color-pale-stone)]">Recent system events</div><Link to="/events" className="mono text-[var(--color-warm-granite)]">View all →</Link></div><div className="grid gap-5 md:grid-cols-3">{data.recentEvents.slice(0, 3).map((event) => <article key={event.id} className="panel p-5"><div className="flex items-center justify-between"><span className="mono text-[var(--color-signal-orange)]">{event.type.replaceAll('_', ' ')}</span><i className="signal" /></div><div className="mt-8 text-2xl tracking-[-.025em]">{event.action.replaceAll('_', ' ')}</div><p className="mt-4 text-sm leading-5 text-[var(--color-warm-granite)]">{event.summary}</p></article>)}</div></section>
    </div>
  </>;
}
