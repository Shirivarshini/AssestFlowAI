# AssetFlow AI

AssetFlow AI is a hackathon MVP for tracking physical assets through their
supply-chain lifecycle and reassessing risk and financing as events occur.

## Active applications

- `ASSETFLOW-AI/` — React/Vite frontend with offline demo and live API modes.
- `backend/` — FastAPI, SQLAlchemy and PostgreSQL application.
- `assetflow-data/` — standalone reconciliation and provenance package.
- `New folder/` — preserved finance-engine prototype; it is not used by the
  integrated application.

## Integrated local setup

1. Start Docker Desktop.
2. In `backend/`, run `docker compose up --build`.
3. Run `docker compose exec backend python -m app.seed`.
4. Copy `ASSETFLOW-AI/.env.example` to `ASSETFLOW-AI/.env.local`.
5. In `ASSETFLOW-AI/`, run `npm.cmd install` and `npm.cmd run dev`.
6. Open `http://localhost:5173`.

The API is served at `http://localhost:8000/api/v1`; OpenAPI documentation is
available at `http://localhost:8000/docs`.

## Validation

```powershell
cd backend
python -m pytest -q

cd ..\assetflow-data
python -m unittest discover -s tests -v

cd ..\ASSETFLOW-AI
npm.cmd run build
npm.cmd run lint
```

Python validation requires Python 3.11+ and the declared dependencies. The
backend tests can alternatively be run inside the Docker service.
