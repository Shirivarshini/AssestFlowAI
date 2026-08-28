import type { FinancingDecision } from '../../types/api';
import { formatCompactCurrency, formatPercent } from '../../lib/formatters';

export function DecisionPanel({ financing }: { financing: FinancingDecision }) {
  return <section className="panel-light grain overflow-hidden">
    <div className="flex flex-col justify-between gap-6 border-b border-[#b8b3b0] p-7 sm:flex-row sm:items-end sm:p-10">
      <div><div className="mono flex items-center gap-2"><i className="signal" /> Financing decision</div><h2 className="section-title mt-6 max-w-2xl">{financing.recommendedInstrument.replaceAll('_', ' ')}</h2></div>
      <span className="mono rounded-[3px] border border-[#101010] px-3 py-2">{financing.action.replaceAll('_', ' ')}</span>
    </div>
    <div className="grid lg:grid-cols-[1.2fr_.8fr]">
      <div className="p-7 sm:p-10"><div className="mono text-[#4d4947]">Recommended amount</div><div className="mt-5 text-[clamp(48px,8vw,72px)] leading-none tracking-[-.04em]">{formatCompactCurrency(financing.recommendedAmount)}</div><div className="mt-10 grid gap-6 border-t border-[#b8b3b0] pt-6 sm:grid-cols-2"><Metric label="Maximum safe" value={formatCompactCurrency(financing.maximumSafeAmount)} /><Metric label="Existing exposure" value={formatCompactCurrency(financing.existingExposure)} /></div></div>
      <div className="border-t border-[#b8b3b0] p-7 lg:border-l lg:border-t-0 sm:p-10"><div className="grid gap-7"><Metric label="Risk class" value={financing.riskLevel} /><Metric label="Confidence" value={formatPercent(financing.confidence)} /><Metric label="Financing required" value={financing.financingRequired ? 'Yes' : 'No'} /><Metric label="Available capacity" value={formatCompactCurrency(financing.availableCapacity ?? Math.max(0, financing.maximumSafeAmount - financing.existingExposure))} /></div></div>
    </div>
    <div className="border-t border-[#b8b3b0] p-7 sm:p-10"><div className="mono text-[#4d4947]">Decision evidence</div><div className="mt-5 grid gap-3 md:grid-cols-2">{financing.decisionFactors.map((factor) => <div key={factor} className="flex gap-3 text-sm leading-5"><i className="signal mt-1.5 shrink-0" />{factor}</div>)}</div><div className="mt-8 grid gap-4 md:grid-cols-2"><Control label="Duplicate financing" blocked={financing.duplicateCheck?.duplicate_detected ?? false} text={financing.duplicateCheck?.reason ?? 'No overlapping claim detected.'} /><Control label="Over-leverage" blocked={financing.leverageCheck?.over_leveraged ?? false} text={financing.leverageCheck?.over_leveraged ? `Excess: ${formatCompactCurrency(financing.leverageCheck.excess_amount)}` : 'Exposure remains within safe capacity.'} /></div></div>
  </section>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div><div className="mono text-[#4d4947]">{label}</div><div className="mt-3 text-2xl tracking-[-.025em]">{value}</div></div>; }
function Control({ label, blocked, text }: { label: string; blocked: boolean; text: string }) { return <div className="border border-[#b8b3b0] p-4"><div className={`mono ${blocked ? 'text-[var(--color-signal-orange)]' : 'text-[#4d4947]'}`}>{label} / {blocked ? 'Review' : 'Clear'}</div><p className="mt-3 text-sm leading-5">{text}</p></div>; }
