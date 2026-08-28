import type { Alert, Asset, AssetDetailResponse, AssetEvent, AuditEntry, DashboardResponse, DecisionAction, EventTriggerResult, EventType, EvidenceEntry, ExposureSummary, FinancingDecision, LifecycleStage, OrchestrationResult, ReconciliationResult, RiskAssessment, RiskLevel, SimulationResult, TimelineStage } from '../types/api';
import * as demoApi from './demoApi';

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '');
const isDemoMode = import.meta.env.VITE_API_MODE === 'demo' || !configuredBaseUrl;
const apiRoot = configuredBaseUrl
  ? (configuredBaseUrl.endsWith('/api/v1') ? configuredBaseUrl : `${configuredBaseUrl}/api/v1`)
  : '/api/v1';

type RawAsset = { id: string; product_name: string; owner_id: string | null; current_lifecycle_stage: string; current_estimated_value: number | null; currency: string };
type RawRisk = { overall_score: number; risk_level: string; components: Record<string, number>; confidence: number; triggers: string[] };
type RawFinancing = { asset_id: string; financing_required: boolean; recommended_instrument: string | null; maximum_safe_amount: number; recommended_amount: number; existing_exposure?: number; available_capacity?: number; risk_level: string; confidence: number; action: string; decision_factors: string[]; duplicate_check?: FinancingDecision['duplicateCheck']; leverage_check?: FinancingDecision['leverageCheck'] };
type RawTransaction = { id: string; instrument: string; principal: number; outstanding_amount: number; status: string; start_date: string };
type RawEvent = { id: string; asset_id: string; event_type: string; event_time: string; severity: string | null; from_stage: string | null; to_stage: string | null };
type RawConflict = { id: string; asset_id: string; source_a: string; source_b: string; field: string; value_a: string | null; value_b: string | null; resolution_status: string; resolution_reason: string | null; confidence: number | null };
type RawAlert = { id: string; asset_id: string; alert_type: string; severity: string; message: string; created_at: string };
type RawDecision = { id: string; asset_id: string; recommendation: string; decision_factors: string[] | null; confidence: number | null; created_at: string };
type RawDashboard = { asset_counts: Record<string, number>; total_exposure: number; financing_opportunities: number; risk_alerts: number; recent_events: RawEvent[]; financing_transitions: RawTransaction[] };

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiRoot}${endpoint}`, { ...options, headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: { message?: string } } | null;
    throw new Error(body?.error?.message ?? `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

const riskLevel = (value: string): RiskLevel => (['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].includes(value) ? value : 'MEDIUM') as RiskLevel;
const decisionAction = (value: string): DecisionAction => (value === 'INCREASE' ? 'INCREASE_LIMIT' : (['MAINTAIN', 'REDUCE_EXPOSURE', 'SETTLE', 'TRANSITION', 'NEEDS_REVIEW', 'BLOCK'].includes(value) ? value : 'NEEDS_REVIEW')) as DecisionAction;
const exposure = (items: RawTransaction[]) => items.filter((item) => ['ACTIVE', 'REDUCED'].includes(item.status)).reduce((sum, item) => sum + item.outstanding_amount, 0);

function mapTimeline(current: string, events: RawEvent[]): TimelineStage[] {
  const stages: LifecycleStage[] = ['PURCHASE_ORDER', 'RAW_MATERIAL', 'PRODUCTION', 'FINISHED_GOODS', 'SHIPMENT', 'WAREHOUSE', 'DELIVERY', 'INVOICE', 'RECEIVABLE', 'CASH_REALISATION'];
  const currentIndex = Math.max(0, stages.indexOf(current as LifecycleStage));
  return stages.map((stage, index) => ({
    stage,
    label: stage.replaceAll('_', ' ').toLowerCase().replace(/^./, (letter) => letter.toUpperCase()),
    status: index < currentIndex ? 'completed' : index === currentIndex ? 'current' : 'upcoming',
    date: events.find((event) => event.to_stage === stage)?.event_time.slice(0, 10) ?? '',
  }));
}

function mapRisk(assetId: string, raw: RawRisk): RiskAssessment {
  return { assetId, score: raw.overall_score, level: riskLevel(raw.risk_level), components: Object.entries(raw.components).map(([label, value]) => ({ label: label.replaceAll('_', ' '), value })), triggers: raw.triggers };
}

function mapFinancing(raw: RawFinancing, existingExposure = 0): FinancingDecision {
  return { assetId: raw.asset_id, financingRequired: raw.financing_required, recommendedInstrument: raw.recommended_instrument ?? 'NONE', maximumSafeAmount: raw.maximum_safe_amount, recommendedAmount: raw.recommended_amount, existingExposure: raw.existing_exposure ?? existingExposure, availableCapacity: raw.available_capacity, duplicateCheck: raw.duplicate_check, leverageCheck: raw.leverage_check, riskLevel: riskLevel(raw.risk_level), confidence: Math.round(raw.confidence * 100), action: decisionAction(raw.action), decisionFactors: raw.decision_factors };
}

function mapAsset(raw: RawAsset, risk: RawRisk, financing: RawFinancing, transactions: RawTransaction[], events: RawEvent[]): Asset {
  const existingExposure = exposure(transactions);
  return { id: raw.id, name: raw.id, product: raw.product_name, owner: raw.owner_id ?? 'Unassigned', currentStage: raw.current_lifecycle_stage as LifecycleStage, currentStageLabel: raw.current_lifecycle_stage.replaceAll('_', ' '), currentValue: raw.current_estimated_value ?? 0, currency: raw.currency, riskScore: risk.overall_score, riskLevel: riskLevel(risk.risk_level), existingExposure, financingNeed: financing.recommended_amount, confidence: Math.round(risk.confidence * 100), physicalState: 'Tracked', financialState: existingExposure ? `${raw.currency} ${existingExposure.toLocaleString()} financed` : 'Unfinanced', contractualState: 'Active', timeline: mapTimeline(raw.current_lifecycle_stage, events) };
}

function mapEvent(raw: RawEvent): AssetEvent {
  return { id: raw.id, type: raw.event_type as EventType, assetId: raw.asset_id, timestamp: raw.event_time, severity: (['LOW', 'MEDIUM', 'HIGH'].includes(raw.severity ?? '') ? raw.severity : 'MEDIUM') as 'LOW' | 'MEDIUM' | 'HIGH', before: { risk: 0, financing: 0 }, after: { risk: 0, financing: 0 }, action: 'MAINTAIN', summary: `${raw.event_type.replaceAll('_', ' ')}${raw.to_stage ? ` moved asset to ${raw.to_stage.replaceAll('_', ' ')}` : ''}.` };
}

function mapConflicts(assetId: string, conflicts: RawConflict[]): ReconciliationResult {
  const first = conflicts[0];
  return { assetId, canonicalValue: first?.value_a ?? 'No conflict', confidence: Math.round((first?.confidence ?? 1) * 100), resolutionReason: first?.resolution_reason ?? 'All available sources agree.', conflictDetected: conflicts.length > 0, sources: conflicts.map((item) => ({ source: item.source_a, field: item.field, values: { [item.source_a]: item.value_a ?? '', [item.source_b]: item.value_b ?? '' } })) };
}

function mapAlert(raw: RawAlert): Alert {
  const severity = raw.severity === 'CRITICAL' ? 'HIGH' : raw.severity === 'WARNING' ? 'MEDIUM' : 'LOW';
  return { id: raw.id, assetId: raw.asset_id, title: raw.alert_type.replaceAll('_', ' '), message: raw.message, severity, createdAt: raw.created_at, status: (raw as RawAlert & { status?: Alert['status'] }).status ?? 'OPEN' };
}

async function realFinancing(assetId: string): Promise<FinancingDecision> {
  const [evaluation, transactions] = await Promise.all([request<RawFinancing>(`/assets/${assetId}/financing/evaluation`), request<RawTransaction[]>(`/assets/${assetId}/financing`)]);
  return mapFinancing(evaluation, exposure(transactions));
}

export async function getDefaultAssetId(): Promise<string> {
  if (isDemoMode) return 'AST-1001';
  const assets = await request<RawAsset[]>('/assets');
  if (!assets.length) throw new Error('No assets exist yet. Run the backend seed command first.');
  return assets[0].id;
}

async function resolveAssetId(assetId: string): Promise<string> {
  return !isDemoMode && assetId === 'AST-1001' ? getDefaultAssetId() : assetId;
}

export async function getDashboard(): Promise<DashboardResponse> {
  if (isDemoMode) return demoApi.getDashboard();
  const [dashboard, assets] = await Promise.all([request<RawDashboard>('/dashboard'), request<RawAsset[]>('/assets')]);
  if (!assets.length) throw new Error('No assets exist yet. Run the backend seed command first.');
  const detail = await getAsset(assets[0].id);
  return { assetCount: Object.values(dashboard.asset_counts).reduce((sum, count) => sum + count, 0), totalExposure: dashboard.total_exposure, financingOpportunities: dashboard.financing_opportunities, riskAlerts: dashboard.risk_alerts, primaryAsset: detail.asset, recentEvents: dashboard.recent_events.map(mapEvent), financingTransitions: dashboard.financing_transitions.map((item) => ({ from: 'ACTIVE', to: item.status, label: item.instrument })) };
}

export async function getAsset(assetId: string): Promise<AssetDetailResponse> {
  if (isDemoMode) return demoApi.getAsset(assetId);
  const id = await resolveAssetId(assetId);
  const [asset, risk, financing, transactions, timeline, decisions, alerts, conflicts] = await Promise.all([
    request<RawAsset>(`/assets/${id}`), request<RawRisk>(`/assets/${id}/risk`), request<RawFinancing>(`/assets/${id}/financing/evaluation`), request<RawTransaction[]>(`/assets/${id}/financing`), request<{ events: RawEvent[] }>(`/assets/${id}/timeline`), request<RawDecision[]>(`/assets/${id}/decisions`), request<RawAlert[]>('/alerts'), request<RawConflict[]>(`/assets/${id}/conflicts`),
  ]);
  const latest = decisions[0];
  return {
    asset: mapAsset(asset, risk, financing, transactions, timeline.events), risk: mapRisk(id, risk), financing: mapFinancing(financing, exposure(transactions)),
    aiDecision: latest ? { id: latest.id, assetId: id, status: latest.recommendation, summary: latest.recommendation, factors: latest.decision_factors ?? [], confidence: Math.round((latest.confidence ?? 0) * 100) } : { id: 'pending', assetId: id, status: 'PENDING', summary: 'No recorded AI decision yet.', factors: [], confidence: 0 },
    alerts: alerts.filter((item) => item.asset_id === id).map(mapAlert), sourceEvidence: mapConflicts(id, conflicts),
    financingHistory: transactions.map((item) => ({ id: item.id, instrument: item.instrument, amount: item.principal, status: item.status, date: item.start_date })),
    auditHistory: decisions.map((item) => ({ id: item.id, summary: item.recommendation, createdAt: item.created_at })),
  };
}

export async function getFinancing(assetId: string) { return isDemoMode ? demoApi.getFinancing(assetId) : realFinancing(await resolveAssetId(assetId)); }
export async function getRisk(assetId: string) { const id = await resolveAssetId(assetId); return isDemoMode ? demoApi.getRisk(id) : mapRisk(id, await request<RawRisk>(`/assets/${id}/risk`)); }
export async function getReconciliation(assetId: string) { const id = await resolveAssetId(assetId); return isDemoMode ? demoApi.getReconciliation(id) : mapConflicts(id, await request<RawConflict[]>(`/assets/${id}/conflicts`)); }
export async function getAlerts() { return isDemoMode ? demoApi.getAlerts() : (await request<RawAlert[]>('/alerts')).map(mapAlert); }
export async function updateAlert(alertId: string, status: 'ACKNOWLEDGED' | 'RESOLVED'): Promise<Alert> {
  if (isDemoMode) return { ...(await demoApi.getAlerts()).find((item) => item.id === alertId)!, status };
  return mapAlert(await request<RawAlert>(`/alerts/${alertId}`, { method: 'PATCH', body: JSON.stringify({ status }) }));
}
export async function getEvents() { return isDemoMode ? demoApi.getEvents() : (await request<RawEvent[]>('/events')).map(mapEvent); }

export async function triggerEvent(assetId: string, eventType: EventType): Promise<EventTriggerResult> {
  if (isDemoMode) return demoApi.triggerEvent(assetId, eventType);
  const id = await resolveAssetId(assetId);
  const before = await getAsset(id);
  const event = await request<RawEvent>(`/assets/${id}/events`, { method: 'POST', body: JSON.stringify({ event_type: eventType }) });
  const detail = await getAsset(id);
  return {
    event: {
      ...mapEvent(event),
      before: { risk: before.risk.score, financing: before.financing.recommendedAmount },
      after: { risk: detail.risk.score, financing: detail.financing.recommendedAmount },
      action: detail.financing.action,
    },
    asset: detail.asset,
    risk: detail.risk,
    financing: detail.financing,
  };
}

export async function getExposure(assetId = 'AST-1001'): Promise<ExposureSummary> {
  const id = await resolveAssetId(assetId);
  if (isDemoMode) {
    const financing = await demoApi.getFinancing(id);
    return { asset_id: id, total_principal: financing.existingExposure, total_outstanding: financing.existingExposure, active_financing_count: financing.existingExposure ? 1 : 0, available_safe_capacity: Math.max(0, financing.maximumSafeAmount - financing.existingExposure), maximum_safe_exposure: financing.maximumSafeAmount, utilization_percentage: financing.maximumSafeAmount ? financing.existingExposure / financing.maximumSafeAmount * 100 : 0, currency: 'INR', updated_at: new Date().toISOString() };
  }
  return request<ExposureSummary>(`/assets/${id}/exposure`);
}

export async function getAudit(assetId?: string): Promise<AuditEntry[]> {
  if (isDemoMode) return [{ id: 'AUD-DEMO-1', asset_id: 'AST-1001', actor: 'SYSTEM', action: 'DEMO_STATE_INITIALIZED', details: { data_mode: 'SIMULATED' }, created_at: new Date().toISOString() }];
  return request<AuditEntry[]>(assetId ? `/assets/${await resolveAssetId(assetId)}/audit` : '/audit');
}

export async function getEvidence(assetId = 'AST-1001'): Promise<EvidenceEntry[]> {
  const id = await resolveAssetId(assetId);
  if (isDemoMode) return [{ id: 'SRC-DEMO-1', asset_id: id, source: 'SIMULATOR', field: 'physical_state', value: 'IN_TRANSIT', received_at: new Date().toISOString(), reliability: 0.8, raw_payload: { simulated: true }, data_mode: 'SIMULATED' }];
  return request<EvidenceEntry[]>(`/assets/${id}/evidence`);
}

export async function orchestrate(assetId = 'AST-1001', trigger = 'MANUAL'): Promise<OrchestrationResult> {
  const id = await resolveAssetId(assetId);
  if (isDemoMode) {
    const [risk, financing] = await Promise.all([demoApi.getRisk(id), demoApi.getFinancing(id)]);
    return { asset_id: id, trigger, state_summary: { lifecycle_stage: 'SHIPMENT', data_mode: 'SIMULATED' }, risk: { risk_score: risk.score, risk_level: risk.level, confidence: financing.confidence / 100, triggers: risk.triggers, recommended_next_step: financing.action }, financing: { ...financing, existing_exposure: financing.existingExposure, available_capacity: Math.max(0, financing.maximumSafeAmount - financing.existingExposure), eligible_instruments: [financing.recommendedInstrument] }, duplicate_check: { duplicate_detected: false, severity: 'LOW', reason: 'No duplicate detected.', recommended_action: 'ALLOW' }, leverage_check: { over_leveraged: false, severity: 'LOW', excess_amount: 0, action: 'ALLOW' }, decision: { action: financing.action, amount: financing.recommendedAmount, instrument: financing.recommendedInstrument, confidence: financing.confidence / 100, factors: financing.decisionFactors }, explanation: { mode: 'DETERMINISTIC_TEMPLATE', summary: `${financing.action} financing based on the current simulated state.`, key_factors: financing.decisionFactors, blocking_conditions: [], disclaimer: 'Prototype decision support only; this is not a lending approval.' } };
  }
  return request<OrchestrationResult>(`/assets/${id}/orchestrate`, { method: 'POST', body: JSON.stringify({ trigger }) });
}

export async function simulateEvent(assetId: string, eventType: string): Promise<SimulationResult> {
  const id = await resolveAssetId(assetId);
  if (isDemoMode) {
    const before = await orchestrate(id, 'BEFORE_EVENT');
    await demoApi.triggerEvent(id, eventType as EventType);
    const after = await orchestrate(id, eventType);
    return { event: { event_type: eventType, data_mode: 'SIMULATED' }, before, after, alert: null };
  }
  return request<SimulationResult>('/events/simulate', { method: 'POST', body: JSON.stringify({ asset_id: id, event_type: eventType }) });
}
