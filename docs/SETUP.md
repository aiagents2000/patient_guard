# PatientGuard — Setup Guide

## Prerequisiti

- Python 3.11+
- Node.js 18+
- npm 9+

## 1. Clone e setup

```bash
git clone https://github.com/aiagents2000/patient_guard.git
cd patient_guard
```

## 2. Backend

### Installare dipendenze Python

```bash
cd backend
pip install -r requirements.txt
```

### Generare dati sintetici e trainare i modelli

Questo step è necessario solo la prima volta (o se vuoi rigenerare i dati):

```bash
# Genera 1000 pazienti sintetici
cd ../data
python3 generate_synthea.py

# Preprocessa il dataset per il ML
python3 preprocess.py

# Genera il JSON demo per il frontend
python3 seed_db.py --mode json

# Traina i 3 modelli XGBoost
cd ../backend
python3 -m ml.train --data ../data/processed/ml_dataset.csv
```

### Avviare il server API

```bash
cd backend
python3 -m uvicorn main:app --reload --port 8000
```

Il server si avvia su `http://localhost:8000`. Documentazione API interattiva su `http://localhost:8000/docs`.

### Configurazione opzionale

Crea un file `backend/.env` per configurare servizi esterni (opzionali):

```env
# Supabase (se non configurato, usa JSON demo)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# LLM per riassunti clinici (se non configurato, usa regole)
OPENAI_API_KEY=sk-...
# oppure
ANTHROPIC_API_KEY=sk-ant-...
```

## 3. Frontend

### Installare dipendenze Node

```bash
cd frontend
npm install
```

### Configurare environment

```bash
cp .env.local.example .env.local
```

Il file `.env.local` contiene `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` — modifica se il backend è su un altro host.

### Avviare il server di sviluppo

```bash
npm run dev
```

Il frontend si avvia su `http://localhost:3000`.

## 4. Pagine disponibili

| Pagina | URL | Descrizione |
|--------|-----|-------------|
| Login | `/login` | Accesso demo (credenziali pre-compilate) |
| Dashboard | `/dashboard` | Panoramica pazienti e statistiche |
| Pazienti | `/dashboard/patients` | Registro pazienti con filtri |
| Alert | `/dashboard/alerts` | Gestione alert clinici |
| Impostazioni | `/dashboard/settings` | Tema, stato backend, info |
| Dettaglio paziente | `/dashboard/patient/{id}` | Rischio, vitali, cartella clinica, AI summary |
| Portale paziente | `/patient-portal` | Vista paziente (accessibile, tema chiaro) |

## 5. Modalità operative

### Demo mode (default)
Senza Supabase configurato, il backend carica i dati da `data/sample/synthetic_patients.json` (30 pazienti). Tutti gli endpoint funzionano normalmente.

### Production mode
Con Supabase configurato, il backend legge/scrive dal database PostgreSQL. Esegui `backend/schema.sql` su Supabase per creare le tabelle, poi `python3 data/seed_db.py --mode db` per popolare i dati.
