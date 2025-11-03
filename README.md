## Binance Analytics Project Skeleton

This repository contains the initial scaffolding for a full-stack Binance analytics application. It wires up a Python FastAPI backend, a React + Tailwind (Vite) frontend, shared analytics utilities, and helper scripts so you can focus on implementing the real-time ingestion, quantitative analytics, and dashboards.

### What's Included
- FastAPI app with modular routers (`health`, `data`, `analytics`, `alerts`) and stubs ready for implementation.
- Binance WebSocket ingestion service with in-memory buffers, async queue, persistence flush worker, and live metrics broadcaster.
- Analytics helpers for hedge ratio (OLS), spreads, z-score, rolling correlation, and ADF tests wired to REST endpoints.
- React + Vite + Tailwind frontend with Plotly charts, alert management UI, CSV upload/export, and live metrics via WebSocket.
- `run_all.ps1` script to launch backend and frontend together on Windows.

### Quick Start
1. **Backend dependencies**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   ```
2. **Frontend dependencies**
   ```powershell
   cd frontend
   npm install
   ```
3. **Run both services**
   ```powershell
   cd ..
   ./run_all.ps1
   ```
   Backend is available at `http://localhost:8000` and frontend at `http://localhost:5173`.

### Project Structure
```
backend/        # FastAPI application, ingestion services, analytics modules
frontend/       # Vite React app with Tailwind styling
diagrams/       # Architecture diagrams (add draw.io + exported images here)
tests/          # Test suite placeholder
run_all.ps1     # Helper script to start backend + frontend concurrently
```

### Next Steps
- Extend analytics coverage (e.g. Kalman hedge, backtests) and harden alert evaluation logic.
- Add automated tests for analytics, resampling, and alert triggers under `tests/`.
- Document architecture decisions and analytics methodology in detail, and add the required diagram exports.

### API Highlights
- `GET /api/health` – heartbeat
- `GET /api/data/history` – tick history → OHLCV bars (1s/1m/5m)
- `POST /api/data/upload` – ingest OHLC CSVs for analytics
- `POST /api/analytics/snapshot` – OLS hedge ratio, spread, z-score, rolling correlation, ADF
- `GET /api/ws/live` – WebSocket stream of live metrics + alert triggers
- `POST /api/alerts/` – manage alert rules (>, >=, <, <= on spread/zscore/corr/beta)

### Notes
- Tailwind utilities live in `frontend/src/styles/tailwind.css`.
- Default live metrics stream publishes for the first two configured symbols (tweak `default_symbols` in `backend/core/config.py`).
- Update the README with environment variables, testing commands, analytics methodology, and ChatGPT usage notes as the project evolves.




