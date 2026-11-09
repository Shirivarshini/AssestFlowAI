import { useState } from 'react';
import { Link } from 'react-router-dom';
import sentinel from '../../assets/sentinel.svg';
import type { Asset } from '../../types/api';
import './WorkflowHero.css';

export function WorkflowHero({ asset }: { asset: Asset }) {
  const assetPath = `/assets/${asset.id}`;
  const workflows = [
    {
      label: 'Track',
      headline: ['ORDERS.', 'ASSETS.', 'STATE.'],
      description: 'Follow physical assets from purchase order through production, delivery, and cash realisation.',
      action: 'Inspect asset',
      path: assetPath,
      telemetry: 'Lifecycle telemetry',
    },
    {
      label: 'Verify',
      headline: ['ASSETS.', 'SIGNALS.', 'VALUE.'],
      description: 'See the whole supply chain. Asset state, source evidence, and financing exposure come together in one view.',
      action: 'Reconcile sources',
      path: '/reconciliation',
      telemetry: 'Evidence reconciliation',
    },
    {
      label: 'Assess',
      headline: ['RISK.', 'LIMITS.', 'SIGNALS.'],
      description: 'See where risk is rising and which changes need attention before exposure moves beyond policy.',
      action: 'View risk alerts',
      path: '/alerts',
      telemetry: 'Risk monitoring',
    },
    {
      label: 'Finance',
      headline: ['VALUE.', 'CAPACITY.', 'CAPITAL.'],
      description: 'Review financing capacity against the asset’s verified state, current value, and outstanding exposure.',
      action: 'Review financing',
      path: `${assetPath}/financing`,
      telemetry: 'Financing assessment',
    },
    {
      label: 'Monitor',
      headline: ['EVENTS.', 'IMPACT.', 'ACTION.'],
      description: 'Trace material events and see how each change affects risk, funding capacity, and the next decision.',
      action: 'Open event monitor',
      path: '/events',
      telemetry: 'Event monitoring',
    },
  ];
  const [selected, setSelected] = useState(1);
  const workflow = workflows[selected];
  const step = String(selected + 1).padStart(2, '0');

  return (
    <section className="workflow-hero" aria-labelledby="workflow-title">
      <div className="workflow-inner">
        <div className="workflow-rail" role="group" aria-label="AssetFlow workflows">
          {workflows.map(({ label }, index) => (
            <button
              type="button"
              key={label}
              className="workflow-step mono"
              aria-pressed={selected === index}
              aria-controls="workflow-copy"
              onClick={() => setSelected(index)}
            >
              <span>0{index + 1}</span> {label}
            </button>
          ))}
        </div>

        <div id="workflow-copy" className="workflow-copy" aria-live="polite">
          <div key={workflow.label} className="workflow-reveal">
            <p className="mono workflow-eyebrow">{step} / {workflow.label}</p>
            <h1 id="workflow-title" className="workflow-title">
              {workflow.headline.map((line) => <span key={line}>{line}</span>)}
            </h1>
            <p className="workflow-description">{workflow.description}</p>
            <Link className="control mono console-action" to={workflow.path}>
              {workflow.action}<span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>

        <div className="workflow-scene" aria-hidden="true">
          <svg className="workflow-circuit" viewBox="0 0 780 92" preserveAspectRatio="none">
            <path d="M0 48h118l24-25h400l17 17h171" />
            <path d="M354 23h24M559 40v48" className="workflow-circuit-hot" />
            <circle cx="559" cy="40" r="3" />
          </svg>
          <div className="workflow-readout mono">
            <div className="workflow-readout-icon">⌘</div>
            <div className="workflow-readout-text">
              <span>{workflow.telemetry}</span>
              <span>Primary asset / {asset.id}</span>
            </div>
          </div>
          <div className="workflow-state mono">
            <span>Asset status —</span>
            <strong>{asset.currentStageLabel}</strong>
          </div>
          <img className="workflow-sentinel" src={sentinel} alt="" fetchPriority="high" />
          <div key={workflow.label} className="workflow-sweep" />
          <div className="workflow-sight" />
          <div className="workflow-instruments mono">
            <span>01 / Asset state</span>
            <span>02 / Source evidence</span>
            <span>03 / Risk &amp; capital</span>
          </div>
          <div className="workflow-caption mono">
            <span><b>{step} / 05</b> {workflow.telemetry}</span>
            <span><i className="signal" /> Record loaded</span>
          </div>
        </div>
      </div>
    </section>
  );
}
