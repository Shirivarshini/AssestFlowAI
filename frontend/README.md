# AssetFlow AI frontend

React 19 + TypeScript + Vite frontend for the AssetFlow supply-chain finance demo.

## Run in demo mode

Demo mode is the default and requires no backend:

```powershell
npm.cmd install
npm.cmd run dev
```

## Run against FastAPI

Copy `.env.example` to `.env.local`, then start Vite. `VITE_API_BASE_URL`
accepts either `http://localhost:8000` or `http://localhost:8000/api/v1`.

```powershell
Copy-Item .env.example .env.local
npm.cmd run dev
```

The client translates the backend's snake_case DTOs into typed UI view
models. To force local fixtures, set `VITE_API_MODE=demo` or omit the API URL.

## Validate

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd test
```

Operational routes added for the complete demo are `/alerts`, `/audit`, and
`/simulator`. The simulator runs the same structured flow in both live API and
clearly-labeled offline demo modes, and immediately presents before/after risk
and financing decisions.
