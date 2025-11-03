## Binance Futures Analytics (FastAPI + React)

Production-ready, real-time analytics app:
- FastAPI backend (ingestion, persistence, analytics, alerts, WebSocket)
- React + Vite + Tailwind frontend (Plotly charts, alerts, CSV upload/export)

### Run (Windows)
1) Backend
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

2) Frontend
```powershell
cd frontend
npm install
npm run dev
```

Backend: `http://localhost:8000`  Frontend: `http://localhost:5173`

### .env (optional)
Create `.env` in repo root:
```env
APP_NAME=Binance Analytics Backend
DATA_DIR=data
SQLITE_PATH=data/ticks.db
LOG_LEVEL=INFO
DEFAULT_SYMBOLS=btcusdt,ethusdt
TICK_BUFFER_SIZE=3600
DB_FLUSH_INTERVAL_SECONDS=2.0
DB_BATCH_SIZE=200
ANALYTICS_WINDOW=300
```

### Key Endpoints
- `GET /api/data/history?symbol=btcusdt&timeframe=1s`
- `POST /api/data/upload` (CSV: timestamp,open,high,low,close,volume)
- `GET /api/data/export?symbol=btcusdt&timeframe=1s`
- `POST /api/analytics/snapshot` (pair analytics: β, spread, z, corr, ADF)
- `GET /api/ws/live` (live metrics stream)
- `POST /api/alerts` / `PUT /api/alerts/{id}/toggle` / `DELETE /api/alerts/{id}`

### Verify Quickly
1) Wait ~30s after startup for ticks; charts should populate
2) Change timeframe (1s/1m) and confirm overlays update
3) Create an alert (e.g., z-score > 2); observe triggers in panel
4) Upload `test_sample_data.csv`; see preview rows
5) Export CSV from current symbol/timeframe

### Troubleshooting
- TypeScript: install missing deps
```powershell
cd frontend
npm i axios @types/axios @tanstack/react-query @tanstack/react-query-devtools react-plotly.js plotly.js
```
- React 18 import issues: use named imports (`StrictMode`, `createRoot`)
- GeoJSON types: ensure tsconfig types includes only `vite/client`; if needed `npm i -D @types/geojson`
- Pydantic v2: use `pydantic-settings`; ensure `pydantic-settings>=2`
- NaN JSON errors: ensure analytics convert NaN/Inf → null (already handled)

### Git Hygiene
- `.gitignore` includes Python/Node artifacts (`node_modules/`, `.venv/`, `data/`, `__pycache__/`, `.env`, `dist/`)
- Unstage mistakenly added files: `git reset` (to unstage), then update `.gitignore`

### Commit Message (suggestion)
```
feat(fullstack): live ingestion, analytics endpoints, WebSocket stream, React dashboard with Plotly, alerts, CSV import/export; docs + report
```

### Report & PDF
- Full report: `PROJECT_REPORT.md` (includes prompts used)
- Convert to PDF (VS Code): install "Markdown PDF" → right-click file → Export (pdf)

### Structure
```
backend/   # FastAPI app, services (ingest, persistence, live, alerts), analytics
frontend/  # React (Vite, Tailwind, Plotly, React Query)
diagrams/  # Architecture diagrams
data/      # SQLite DB and exports
```




