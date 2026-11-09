import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink, matchPath, useLocation } from 'react-router-dom';

interface AppShellProps { children: ReactNode }

const navItems = [
  { to: '/assets/AST-1001', label: 'Asset' },
  { to: '/reconciliation', label: 'Sources' },
  { to: '/events', label: 'Events' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/audit', label: 'Audit' },
];

export function AppShell({ children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const isDashboard = pathname === '/' || Boolean(matchPath('/dashboard', pathname));

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="console-shell">
      <a className="console-skip mono" href="#console-main">Skip to content</a>
      <header className="console-header">
        <div className="console-strip">
          <span>AssetFlow Control · Supply chain intelligence</span>
          <span className="mono">Asset operations / 01</span>
        </div>
        <div className="console-nav-row">
          <Link to="/" className="console-brand" onClick={() => setMenuOpen(false)} aria-label="AssetFlow overview">
            <span className="console-brand-mark" aria-hidden="true"><i /><i /></span>
            AssetFlow <span>AI</span>
          </Link>
          <div className="console-division mono">
            <span aria-hidden="true" className="console-division-mark">⠿</span> Operations console
          </div>
          <button type="button" className="control mono console-menu" onClick={() => setMenuOpen((open) => !open)} aria-expanded={menuOpen} aria-controls="console-navigation">Menu</button>
          <nav id="console-navigation" className="console-navigation" aria-label="Primary navigation" data-open={menuOpen}>
            <Link to="/" className="mono" aria-current={isDashboard ? 'page' : undefined} onClick={() => setMenuOpen(false)}>Overview</Link>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className="mono"
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="console-nav-controls">
            <NavLink to="/simulator" onClick={() => setMenuOpen(false)} className="control console-action mono">Simulate event <span aria-hidden="true">↗</span></NavLink>
          </div>
        </div>
      </header>

      <main id="console-main" tabIndex={-1} className={isDashboard ? undefined : 'console-content'}>
        <div key={pathname} className={isDashboard ? undefined : 'frame-in'}>{children}</div>
      </main>

      <footer className="console-footer">
        <div className="console-content grid gap-12 md:grid-cols-[1.5fr_1fr_1fr]">
          <div><div className="mono text-[var(--color-bone)]">AssetFlow / AI</div><p className="mt-5 max-w-sm text-sm leading-6 text-[var(--color-warm-granite)]">Continuous asset intelligence from purchase order to cash realisation.</p></div>
          <div><div className="mono mb-5">Console</div><div className="grid gap-3 text-sm text-[var(--color-warm-granite)]"><NavLink to="/">Overview</NavLink><NavLink to="/assets/AST-1001">Asset</NavLink><NavLink to="/events">Events</NavLink></div></div>
          <div><div className="mono mb-5">System</div><div className="grid gap-3 text-sm text-[var(--color-warm-granite)]"><NavLink to="/alerts">Alerts</NavLink><NavLink to="/audit">Audit trail</NavLink><NavLink to="/simulator">Simulator</NavLink></div></div>
        </div>
      </footer>
    </div>
  );
}
