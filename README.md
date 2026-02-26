# PatientGuard — EHR Risk Intelligence Platform

Piattaforma AI di analisi predittiva delle cartelle cliniche elettroniche (EHR) per il Sistema Sanitario Nazionale italiano.

Progetto sviluppato per l'**HSIL Hackathon 2026** (Harvard Health Systems Innovation Lab), Challenge: Electronic Health Record Analysis.

## Architettura

```
patientguard/
├── backend/              # FastAPI API server
│   ├── ml/               # XGBoost models, training, inference
│   ├── models/           # Data access layer (Supabase + JSON demo)
│   ├── routers/          # API endpoints (patients, alerts, predictions, stats, llm)
│   └── services/         # Alert engine, LLM clinical summaries
├── frontend/             # Next.js 14 dashboard
│   └── src/
│       ├── app/          # Pages: dashboard, patient detail, alerts, settings, portal, login
│       ├── components/   # UI components (charts, tables, sidebar, theme)
│       └── lib/          # API client, utilities
├── data/                 # Data generation & preprocessing scripts
│   └── sample/           # Demo dataset (30 patients JSON)
└── docs/                 # Documentation
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.13, FastAPI, Pydantic |
| ML | XGBoost, scikit-learn, SHAP explainability |
| Database | Supabase (PostgreSQL) — with JSON demo fallback |
| LLM | OpenAI / Anthropic API — with rule-based fallback |

## Quick Start

### 1. Backend

```bash
./env/Scripts/activate              # activate workspace environment
cd backend
pip install -r requirements.txt     # install dependencies
```
With VSCode run (keeping given order) all configurations with "[Backend]" suffix

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # API URL defaults to localhost:8000
npm run dev
```

### 3. Open

| Page | URL |
|------|-----|
| Login | http://localhost:3000/login |
| Dashboard | http://localhost:3000/dashboard |
| Patient Portal | http://localhost:3000/patient-portal |
| API Docs | http://localhost:8000/docs |

Demo credentials: `dott.rossi@ospedale.it` / `demo2026`

## Features

- **3 ML Models**: Risk score (R²=0.92), Readmission prediction, Length of Stay prediction
- **Clinical Dashboard**: Real-time patient monitoring with risk gauges, trend charts, department analytics
- **Alert System**: Auto-generated alerts for critical vitals, risk increases, readmission warnings
- **Patient Portal**: Accessible, elderly-friendly view with plain-language health summaries
- **AI Summaries**: LLM-generated clinical summaries (with rule-based fallback)
- **Dark/Light Theme**: Toggle between themes, persisted across sessions
- **Mobile Responsive**: Full mobile support with collapsible sidebar

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.
