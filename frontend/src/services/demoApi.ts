import type {
  Alert,
  Asset,
  AssetDetailResponse,
  AssetEvent,
  DashboardResponse,
  EventTriggerResult,
  EventType,
  FinancingDecision,
  ReconciliationResult,
  RiskAssessment,
  TimelineStage,
} from '../types/api';

const timeline: TimelineStage[] = [
  { stage: 'PURCHASE_ORDER', label: 'Purchase order', status: 'completed', date: '2026-08-01' },
  { stage: 'RAW_MATERIAL', label: 'Raw material', status: 'completed', date: '2026-08-04' },
  { stage: 'PRODUCTION', label: 'Production', status: 'completed', date: '2026-08-10' },
  { stage: 'FINISHED_GOODS', label: 'Finished goods', status: 'completed', date: '2026-08-12' },
  { stage: 'SHIPMENT', label: 'Shipment', status: 'current', date: '2026-08-15' },
  { stage: 'WAREHOUSE', label: 'Warehouse', status: 'upcoming', date: '2026-08-18' },
  { stage: 'DELIVERY', label: 'Delivery', status: 'upcoming', date: '2026-08-21' },
  { stage: 'INVOICE', label: 'Invoice', status: 'upcoming', date: '2026-08-24' },
  { stage: 'RECEIVABLE', label: 'Receivable', status: 'upcoming', date: '2026-08-28' },
  { stage: 'CASH_REALISATION', label: 'Cash realisation', status: 'upcoming', date: '2026-09-03' },
];

const baseAsset: Asset = {
  id: 'AST-1001',
  name: 'AST-1001',
  product: 'Industrial Electronics',
  owner: 'ABC Manufacturing',
  currentStage: 'SHIPMENT',
  currentStageLabel: 'Shipment',
  currentValue: 1240000,
  currency: 'INR',
  riskScore: 32,
  riskLevel: 'LOW',
  existingExposure: 420000,
  financingNeed: 260000,
  confidence: 94,
  physicalState: 'Verified',
  financialState: '₹42 L financed',
  contractualState: 'Active',
  timeline,
};

const baseRisk: RiskAssessment = {
  assetId: 'AST-1001',
  score: 32,
  level: 'LOW',
  components: [
    { label: 'Asset / Physical', value: 24 },
    { label: 'Buyer', value: 38 },
    { label: 'Logistics', value: 47 },
    { label: 'Liquidity', value: 29 },
    { label: 'Data Confidence', value: 18 },
    { label: 'Existing Exposure', value: 27 },
  ],
  triggers: ['Shipment status confirmed', 'Buyer risk acceptable', 'No material data conflict'],
};

const baseDecision: FinancingDecision = {
  assetId: 'AST-1001',
  financingRequired: true,
  recommendedInstrument: 'IN_TRANSIT_FINANCING',
  maximumSafeAmount: 680000,
  recommendedAmount: 260000,
  existingExposure: 420000,
  riskLevel: 'LOW',
  confidence: 91,
  action: 'MAINTAIN',
  decisionFactors: [
    'Asset physical state verified',
    'Buyer risk acceptable',
    'Existing exposure considered',
    'Shipment status confirmed',
  ],
};

const baseEvidence: ReconciliationResult = {
  assetId: 'AST-1001',
  canonicalValue: '900 units',
  confidence: 72,
  resolutionReason: 'Telemetry provides the latest physical-state evidence.',
  conflictDetected: true,
  sources: [
    { source: 'ERP', field: 'Quantity', values: { 'ERP': '1000', 'WAREHOUSE': '950', 'TELEMETRY': '900' } },
    { source: 'ERP', field: 'Location', values: { 'ERP': 'WH-04', 'WAREHOUSE': 'WH-04', 'TELEMETRY': 'WH-04' } },
    { source: 'ERP', field: 'Production', values: { 'ERP': 'COMPLETE', 'WAREHOUSE': 'COMPLETE', 'TELEMETRY': '92%' } },
  ],
};

const baseAlerts: Alert[] = [
  {
    id: 'alert-1',
    assetId: 'AST-1001',
    title: 'In-transit exposure within threshold',
    message: 'Shipment is moving as expected with current bank exposure maintained within policy.',
    severity: 'LOW',
    createdAt: '2026-08-28T09:00:00Z',
  },
];

const baseHistory = [
  { id: 'hist-1', instrument: 'IN_TRANSIT_FINANCING', amount: 260000, status: 'Active', date: '2026-08-15' },
  { id: 'hist-2', instrument: 'PROCUREMENT_FINANCING', amount: 410000, status: 'Settled', date: '2026-08-11' },
];

const baseAudit = [
  { id: 'audit-1', summary: 'Shipment milestone validated against logistics and buyer confirmation.', createdAt: '2026-08-15T10:21:00Z' },
  { id: 'audit-2', summary: 'Financing recommendation re-evaluated with updated exposure and risk.', createdAt: '2026-08-14T18:10:00Z' },
];

const baseEvents: AssetEvent[] = [
  {
    id: 'evt-1',
    type: 'SHIPMENT_DELAY',
    assetId: 'AST-1001',
    timestamp: '2026-08-28T06:30:00Z',
    severity: 'HIGH',
    summary: 'Shipment delay detected at port gate.',
    before: { risk: 32, financing: 260000 },
    after: { risk: 61, financing: 70000 },
    action: 'REDUCE_EXPOSURE',
  },
  {
    id: 'evt-2',
    type: 'INVOICE_VERIFIED',
    assetId: 'AST-1001',
    timestamp: '2026-08-24T11:00:00Z',
    severity: 'MEDIUM',
    summary: 'Invoice confirmed; transition to invoice financing remains viable.',
    before: { risk: 42, financing: 320000 },
    after: { risk: 31, financing: 520000 },
    action: 'TRANSITION',
  },
];

const assetState = { asset: structuredClone(baseAsset), risk: structuredClone(baseRisk), financing: structuredClone(baseDecision), evidence: structuredClone(baseEvidence), alerts: [...baseAlerts], events: [...baseEvents] };

function cloneAsset(asset: Asset): Asset {
  return JSON.parse(JSON.stringify(asset)) as Asset;
}

export async function getDashboard(): Promise<DashboardResponse> {
  return {
    assetCount: 12,
    totalExposure: 2840000,
    financingOpportunities: 4,
    riskAlerts: 2,
    primaryAsset: cloneAsset(assetState.asset),
    recentEvents: [...assetState.events],
    financingTransitions: [
      { from: 'PURCHASE ORDER', to: 'PROCUREMENT', label: 'Procurement' },
      { from: 'PROCUREMENT', to: 'INVENTORY', label: 'Inventory' },
      { from: 'INVENTORY', to: 'IN-TRANSIT', label: 'In-transit' },
      { from: 'IN-TRANSIT', to: 'WAREHOUSE', label: 'Warehouse' },
      { from: 'WAREHOUSE', to: 'INVOICE', label: 'Invoice' },
      { from: 'INVOICE', to: 'RECEIVABLE', label: 'Receivables' },
    ],
  };
}

export async function getAsset(assetId: string): Promise<AssetDetailResponse> {
  const asset = assetId === assetState.asset.id ? cloneAsset(assetState.asset) : cloneAsset(baseAsset);
  return {
    asset,
    risk: { ...assetState.risk, assetId },
    financing: { ...assetState.financing, assetId },
    aiDecision: {
      id: 'decision-952',
      assetId,
      status: 'MAINTAIN',
      summary: 'In-transit financing remains appropriate for the current shipment condition.',
      factors: [
        'Physical state verified',
        'Buyer risk acceptable',
        'Existing exposure considered',
        'Shipment status confirmed',
      ],
      confidence: 91,
    },
    alerts: assetState.alerts,
    sourceEvidence: { ...assetState.evidence, assetId },
    financingHistory: baseHistory,
    auditHistory: baseAudit,
  };
}

export async function getFinancing(assetId: string): Promise<FinancingDecision> {
  return { ...assetState.financing, assetId };
}

export async function getRisk(assetId: string): Promise<RiskAssessment> {
  return { ...assetState.risk, assetId };
}

export async function getReconciliation(assetId: string): Promise<ReconciliationResult> {
  return { ...assetState.evidence, assetId };
}

export async function getAlerts(): Promise<Alert[]> {
  return assetState.alerts;
}

export async function getEvents(): Promise<AssetEvent[]> {
  return [...assetState.events];
}

export async function triggerEvent(assetId: string, eventType: EventType): Promise<EventTriggerResult> {
  const beforeRisk = eventType === 'SHIPMENT_DELAY' ? 32 : 41;
  const beforeFinancing = eventType === 'SHIPMENT_DELAY' ? 260000 : 420000;
  const afterRisk = eventType === 'SHIPMENT_DELAY' ? 61 : 66;
  const afterFinancing = eventType === 'SHIPMENT_DELAY' ? 70000 : 120000;
  const action = eventType === 'SHIPMENT_DELAY' ? 'REDUCE_EXPOSURE' : 'TRANSITION';

  const event: AssetEvent = {
    id: `evt-${Date.now()}`,
    type: eventType,
    assetId,
    timestamp: new Date().toISOString(),
    severity: 'HIGH',
    summary: eventType === 'SHIPMENT_DELAY' ? 'Shipment delay detected at transit checkpoint.' : 'Operational event reclassified financing exposure.',
    before: { risk: beforeRisk, financing: beforeFinancing },
    after: { risk: afterRisk, financing: afterFinancing },
    action,
  };

  assetState.events = [event, ...assetState.events].slice(0, 6);
  assetState.asset.riskScore = afterRisk;
  assetState.asset.riskLevel = afterRisk > 55 ? 'HIGH' : 'LOW';
  assetState.asset.existingExposure = afterFinancing;
  assetState.asset.financingNeed = afterFinancing;
  assetState.asset.confidence = 78;
  assetState.risk.score = afterRisk;
  assetState.risk.level = afterRisk > 55 ? 'HIGH' : 'LOW';
  assetState.financing.action = action;
  assetState.financing.recommendedAmount = afterFinancing;
  assetState.financing.maximumSafeAmount = afterRisk > 55 ? 490000 : 680000;
  assetState.financing.decisionFactors = [
    'Event triggered reassessment',
    'Physical state changed downstream',
    'Exposure rebalanced after event',
    'Mitigation decision issued',
  ];

  return {
    event,
    asset: cloneAsset(assetState.asset),
    risk: { ...assetState.risk },
    financing: { ...assetState.financing },
  };
}

export const demoAsset = assetState.asset;
