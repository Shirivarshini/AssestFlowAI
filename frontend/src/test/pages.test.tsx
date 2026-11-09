import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/Dashboard';
import { AssetDetailPage } from '../pages/AssetDetail';
import { FinancingPage } from '../pages/Financing';
import { ReconciliationPage } from '../pages/Reconciliation';
import { EventsPage } from '../pages/Events';
import { AlertsPage } from '../pages/Alerts';
import { AuditPage } from '../pages/Audit';
import { SimulatorPage } from '../pages/Simulator';

afterEach(cleanup);
const renderPage = (page: React.ReactNode) => render(<MemoryRouter>{page}</MemoryRouter>);

describe('judge-facing demo pages', () => {
  it('dashboard renders exposure, risk, and alerts', async () => {
    renderPage(<DashboardPage />);
    expect(await screen.findByText('Total exposure')).toBeInTheDocument();
    expect(screen.getByText('Risk alerts')).toBeInTheDocument();
    expect(screen.getByText('Lifecycle telemetry')).toBeInTheDocument();
  });

  it('routes the selected dashboard workflow to its console', async () => {
    renderPage(<DashboardPage />);
    expect(await screen.findByRole('link', { name: 'Reconcile sources' })).toHaveAttribute('href', '/reconciliation');

    const finance = screen.getByRole('button', { name: /04 Finance/i });
    fireEvent.click(finance);

    expect(finance).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('link', { name: 'Review financing' })).toHaveAttribute('href', '/assets/AST-1001/financing');
    expect(screen.queryByRole('link', { name: 'Reconcile sources' })).not.toBeInTheDocument();
  });

  it('asset detail loads its lifecycle and financing state', async () => {
    renderPage(<AssetDetailPage />);
    expect(await screen.findByText('Lifecycle')).toBeInTheDocument();
    expect(screen.getByText('Financing')).toBeInTheDocument();
  });

  it('financing decision renders capacity controls', async () => {
    renderPage(<FinancingPage />);
    expect(await screen.findByText('Financing decision')).toBeInTheDocument();
    expect(screen.getByText('Available capacity')).toBeInTheDocument();
    expect(screen.getByText(/Duplicate financing/)).toBeInTheDocument();
  });

  it('reconciliation conflict renders', async () => {
    renderPage(<ReconciliationPage />);
    expect(await screen.findByText('Conflict detected')).toBeInTheDocument();
    expect(screen.getByText('Canonical value')).toBeInTheDocument();
  });

  it('event monitor renders before and after fields', async () => {
    renderPage(<EventsPage />);
    expect(await screen.findByText('Material event simulator')).toBeInTheDocument();
    expect(screen.getAllByText('Before').length).toBeGreaterThan(0);
    expect(screen.getAllByText('After').length).toBeGreaterThan(0);
  });

  it('alerts page renders operational alerts', async () => {
    renderPage(<AlertsPage />);
    expect(await screen.findByText('Alert center.')).toBeInTheDocument();
    expect(await screen.findByText('In-transit exposure within threshold')).toBeInTheDocument();
  });

  it('audit page renders decision history and simulated provenance', async () => {
    renderPage(<AuditPage />);
    expect(await screen.findByText('Evidence & audit.')).toBeInTheDocument();
    expect(await screen.findByText('SIMULATED')).toBeInTheDocument();
    expect(screen.getByText('Immutable system history')).toBeInTheDocument();
  });

  it('event simulator action produces a before/after decision', async () => {
    renderPage(<SimulatorPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'SHIPMENT DELAY' }));
    await waitFor(() => expect(screen.getByText('Before → after')).toBeInTheDocument());
    expect(screen.getByText('Explanation')).toBeInTheDocument();
  });
});
