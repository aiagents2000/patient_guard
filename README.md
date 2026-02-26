# PatientGuard — EHR Risk Intelligence Platform

Piattaforma AI di analisi predittiva delle cartelle cliniche elettroniche (EHR) per il Sistema Sanitario Nazionale italiano.

Progetto sviluppato per l'**HSIL Hackathon 2026** (Harvard Health Systems Innovation Lab), Challenge #1: Electronic Health Record Analysis.

## Stack

- **Frontend**: Next.js 14 + React 18 + Tailwind CSS + shadcn/ui
- **Backend**: Python 3.11 + FastAPI
- **ML**: scikit-learn + XGBoost
- **Database**: PostgreSQL (Supabase)
- **LLM**: OpenAI / Anthropic API

## Struttura

```
patientguard/
├── backend/          # FastAPI + ML pipeline
├── frontend/         # Next.js app
├── data/             # Script generazione e preprocessing dati
└── docs/             # Documentazione
```

## Quick Start

Vedi [docs/SETUP.md](docs/SETUP.md) per le istruzioni di setup.
