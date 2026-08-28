import { useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

interface AppShellProps { children: ReactNode }

const navItems = [
  { to: '/', label: 'Overview', end: true },
  { to: '/assets/AST-1001', label: 'Asset' },
  { to: '/reconciliation', label: 'Sources' },
  { to: '/events', label: 'Events' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/audit', label: 'Audit' },
];

export function AppShell({ children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="min-h-screen bg-[var(--color-obsidian-canvas)] text-[var(--color-bone)]">
      <header className="sticky top-0 z-30 border-b border-[var(--color-ash-stroke)] bg-[rgba(16,16,16,.94)]">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-5 lg:px-0">
          <NavLink to="/" className="mono flex items-center gap-3 text-[var(--color-bone)]" aria-label="AssetFlow overview">
            <span className="grid h-7 w-7 place-items-center border border-[var(--color-ash-stroke)] text-[10px]">AF</span>
            AssetFlow / Control
          </NavLink>
          <nav className="hidden items-center gap-7 md:flex" aria-label="Primary navigation">
            {navItems.map((item) => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `mono py-2 transition-colors ${isActive ? 'text-[var(--color-bone)]' : 'text-[var(--color-warm-granite)] hover:text-[var(--color-bone)]'}`}>{item.label}</NavLink>)}
          </nav>
          <div className="hidden items-center gap-3 md:flex">
            <span className="mono flex items-center gap-2 text-[var(--color-pale-stone)]"><i className="signal" /> System live</span>
            <NavLink to="/simulator" className="control control-light mono">Simulate →</NavLink>
          </div>
          <button type="button" className="control mono md:hidden" onClick={() => setMenuOpen((open) => !open)} aria-expanded={menuOpen}>Menu</button>
        </div>
        {menuOpen && <nav className="grid border-t border-[var(--color-ash-stroke)] px-5 py-4 md:hidden">{navItems.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setMenuOpen(false)} className="mono border-b border-[var(--color-carbon-lift)] py-4 text-[var(--color-pale-stone)]">{item.label}</NavLink>)}</nav>}
      </header>

      <main className="mx-auto max-w-[1200px] px-5 pb-24 pt-12 lg:px-0 lg:pt-20">{children}</main>

      <footer className="border-t border-[var(--color-ash-stroke)]">
        <div className="mx-auto grid max-w-[1200px] gap-12 px-5 py-20 md:grid-cols-[1.5fr_1fr_1fr] lg:px-0">
          <div><div className="mono text-[var(--color-bone)]">AssetFlow / AI</div><p className="mt-5 max-w-sm text-sm leading-6 text-[var(--color-warm-granite)]">Continuous asset intelligence from purchase order to cash realisation.</p></div>
          <div><div className="mono mb-5">Console</div><div className="grid gap-3 text-sm text-[var(--color-warm-granite)]"><NavLink to="/">Overview</NavLink><NavLink to="/assets/AST-1001">Asset</NavLink><NavLink to="/events">Events</NavLink></div></div>
          <div><div className="mono mb-5">System</div><div className="grid gap-3 text-sm text-[var(--color-warm-granite)]"><NavLink to="/alerts">Alerts</NavLink><NavLink to="/audit">Audit trail</NavLink><NavLink to="/simulator">Simulator</NavLink></div></div>
        </div>
      </footer>
    </div>
  );
}
