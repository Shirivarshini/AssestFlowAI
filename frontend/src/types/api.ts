export type LifecycleStage =
  | 'PURCHASE_ORDER'
  | 'RAW_MATERIAL'
  | 'PRODUCTION'
  | 'FINISHED_GOODS'
  | 'SHIPMENT'
  | 'WAREHOUSE'
  | 'DELIVERY'
  | 'INVOICE'
  | 'RECEIVABLE'
  | 'CASH_REALISATION';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type DecisionAction = 'MAINTAIN' | 'REDUCE_EXPOSURE' | 'INCREASE_LIMIT' | 'SETTLE' | 'TRANSITION' | 'NEEDS_REVIEW' | 'BLOCK';
export type EventType =
  | 'PRODUCTION_DELAY'
  | 'SHIPMENT_DELAY'
  | 'INVENTORY_DETERIORATION'
  | 'WAREHOUSE_EXCEPTION'
  | 'DELIVERY_CONFIRMED'
  | 'BUYER_RISK_CHANGED'
  | 'RECEIVABLE_DELAY'
  | 'INVOICE_VERIFIED'
  | 'DATA_CONFLICT';

export interface TimelineStage {
  stage: LifecycleStage;
  label: string;
  status: 'completed' | 'current' | 'upcoming';
  date: string;
}

export interface Asset {
  id: string;
  name: string;
  product: string;
  owner: string;
  currentStage: LifecycleStage;
  currentStageLabel: string;
  currentValue: number;
  currency: string;
  riskScore: number;
  riskLevel: RiskLevel;
  existingExposure: number;
  financingNeed: number;
  confidence: number;
  physicalState: string;
  financialState: string;
  contractualState: string;
  timeline: TimelineStage[];
}

export interface RiskComponent {
  label: string;
  value: number;
  description?: string;
}

export interface RiskAssessment {
  assetId: string;
  score: number;
  level: RiskLevel;
  components: RiskComponent[];
  triggers: string[];
}

export interface FinancingDecision {
  assetId: string;
  financingRequired: boolean;
  recommendedInstrument: string;
  maximumSafeAmount: number;
  recommendedAmount: number;
  existingExposure: number;
  riskLevel: RiskLevel;
  confidence: number;
  action: DecisionAction;
  decisionFactors: string[];
  availableCapacity?: number;
  duplicateCheck?: { duplicate_detected: boolean; severity: string; reason: string; recommended_action: string };
  leverageCheck?: { over_leveraged: boolean; severity: string; excess_amount: number; action: string };
}

export interface SourceRecord {
  source: string;
  field: string;
  values: Record<string, string>;
}

export interface ReconciliationResult {
  assetId: string;
  canonicalValue: string;
  confidence: number;
  resolutionReason: string;
  sources: SourceRecord[];
  conflictDetected: boolean;
}

export interface Alert {
  id: string;
  assetId: string;
  title: string;
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  createdAt: string;
  status?: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
}

export interface AIDecision {
  id: string;
  assetId: string;
  status: string;
  summary: string;
  factors: string[];
  confidence: number;
}

export interface FinancingHistoryItem {
  id: string;
  instrument: string;
  amount: number;
  status: string;
  date: string;
}

export interface AuditHistoryItem {
  id: string;
  summary: string;
  createdAt: string;
}

export interface EventStateSnapshot {
  risk: number;
  financing: number;
}

export interface AssetEvent {
  id: string;
  type: EventType;
  assetId: string;
  timestamp: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  before: EventStateSnapshot;
  after: EventStateSnapshot;
  action: DecisionAction;
  summary: string;
}

export interface DashboardResponse {
  assetCount: number;
  totalExposure: number;
  financingOpportunities: number;
  riskAlerts: number;
  primaryAsset: Asset;
  recentEvents: AssetEvent[];
  financingTransitions: Array<{ from: string; to: string; label: string }>;
}

export interface AssetDetailResponse {
  asset: Asset;
  risk: RiskAssessment;
  financing: FinancingDecision;
  aiDecision: AIDecision;
  alerts: Alert[];
  sourceEvidence: ReconciliationResult;
  financingHistory: FinancingHistoryItem[];
  auditHistory: AuditHistoryItem[];
}

export interface EventTriggerResult {
  event: AssetEvent;
  asset: Asset;
  risk: RiskAssessment;
  financing: FinancingDecision;
}

export interface ExposureSummary {
  asset_id: string;
  total_principal: number;
  total_outstanding: number;
  active_financing_count: number;
  available_safe_capacity: number;
  maximum_safe_exposure: number;
  utilization_percentage: number;
  currency: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  asset_id: string | null;
  actor: string;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface EvidenceEntry {
  id: string;
  asset_id: string;
  source: string;
  field: string;
  value: string | null;
  received_at: string;
  reliability: number;
  raw_payload: Record<string, unknown> | null;
  data_mode: 'SIMULATED';
}

export interface OrchestrationResult {
  asset_id: string;
  trigger: string;
  state_summary: Record<string, unknown>;
  risk: { risk_score: number; risk_level: RiskLevel; confidence: number; triggers: string[]; recommended_next_step: string };
  financing: FinancingDecision & { existing_exposure: number; available_capacity: number; eligible_instruments: string[] };
  duplicate_check: { duplicate_detected: boolean; severity: string; reason: string; recommended_action: string };
  leverage_check: { over_leveraged: boolean; severity: string; excess_amount: number; action: string };
  decision: { action: string; amount: number; instrument: string | null; confidence: number; factors: string[] };
  explanation: { mode: string; summary: string; key_factors: string[]; blocking_conditions: string[]; disclaimer: string };
}

export interface SimulationResult {
  event: Record<string, unknown>;
  before: OrchestrationResult;
  after: OrchestrationResult;
  alert: Record<string, unknown> | null;
}
