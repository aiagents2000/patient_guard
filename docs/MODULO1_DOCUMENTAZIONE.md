# Modulo 1: Data Pipeline & ML — Documentazione Completa

## Indice

1. [Panoramica](#1-panoramica)
2. [Struttura File](#2-struttura-file)
3. [Flusso Dati](#3-flusso-dati)
4. [Generatore Dati Sintetici](#4-generatore-dati-sintetici)
5. [Feature Engineering](#5-feature-engineering)
6. [Pipeline di Preprocessing](#6-pipeline-di-preprocessing)
7. [Training Modelli ML](#7-training-modelli-ml)
8. [Inferenza e Spiegabilità](#8-inferenza-e-spiegabilità)
9. [Dati Demo](#9-dati-demo)
10. [Guida Esecuzione](#10-guida-esecuzione)
11. [Decisioni Architetturali](#11-decisioni-architetturali)
12. [Interfaccia con il Modulo 2](#12-interfaccia-con-il-modulo-2)

---

## 1. Panoramica

Il Modulo 1 costruisce l'intera pipeline dati-predizione di PatientGuard: dalla generazione di 1000 pazienti sintetici italiani, all'estrazione di 26 feature cliniche, al training di 3 modelli XGBoost, fino a una pipeline di inferenza con spiegabilità che restituisce i top 5 fattori di rischio per ogni paziente.

**Responsabile:** Persona AI & Data Science (~10h)

**Cosa produce:**
- 8 file CSV con dati sintetici (1000 pazienti, 111k osservazioni)
- 1 dataset ML tabellare (1000 righe × 33 colonne)
- 3 modelli addestrati (.joblib)
- 1 file JSON demo con 30 pazienti completi per il frontend

---

## 2. Struttura File

```
patientguard/
├── backend/
│   ├── __init__.py
│   ├── requirements.txt                    # Dipendenze Python
│   └── ml/
│       ├── __init__.py
│       ├── features.py                     # Feature engineering (467 righe)
│       ├── pipeline.py                     # Preprocessing riutilizzabile (310 righe)
│       ├── train.py                        # Training 3 modelli (424 righe)
│       ├── predict.py                      # Inferenza + spiegabilità (346 righe)
│       └── models/                         # Artefatti generati
│           ├── risk_score_model.joblib     # Modello risk score (1.4 MB)
│           ├── readmission_model.joblib    # Modello readmission (745 KB)
│           ├── los_model.joblib            # Modello LOS (604 KB)
│           ├── preprocessor.joblib         # StandardScaler serializzato (2 KB)
│           ├── feature_importance.json     # Importanza feature (5 KB)
│           └── training_metrics.json       # Metriche performance (402 B)
│
├── data/
│   ├── generate_synthea.py                 # Generatore dati sintetici (810 righe)
│   ├── download_synthea.sh                 # Wrapper shell
│   ├── preprocess.py                       # Preprocessing CSV → dataset ML (389 righe)
│   ├── seed_db.py                          # Generatore JSON demo (377 righe)
│   ├── synthea_output/                     # CSV generati (~21 MB)
│   │   ├── patients.csv                    # 1000 pazienti
│   │   ├── encounters.csv                  # ~4554 ricoveri/visite
│   │   ├── encounters_meta.csv             # Encounters con metadati interni
│   │   ├── conditions.csv                  # ~2569 diagnosi
│   │   ├── medications.csv                 # ~2946 prescrizioni
│   │   ├── observations.csv                # ~111376 osservazioni
│   │   ├── procedures.csv                  # ~2421 procedure
│   │   └── allergies.csv                   # ~208 allergie
│   ├── processed/
│   │   └── ml_dataset.csv                  # 1000 righe × 33 colonne
│   └── sample/
│       └── synthetic_patients.json         # 30 pazienti completi (~112 KB)
```

**Totale codice scritto:** ~2823 righe di Python (6 file)

---

## 3. Flusso Dati

```
┌──────────────────────┐
│ generate_synthea.py  │  Genera 1000 pazienti sintetici italiani
│ (810 righe)          │  con 6 profili clinici coerenti
└────────┬─────────────┘
         │  7 file CSV (Synthea format)
         ▼
┌──────────────────────┐
│ preprocess.py        │  Estrae 26 feature per encounter
│ (389 righe)          │  + 4 target variables
│ usa: features.py     │
│ usa: pipeline.py     │
└────────┬─────────────┘
         │  ml_dataset.csv (1000 × 33)
         ▼
┌──────────────────────┐
│ train.py             │  Addestra 3 modelli XGBoost
│ (424 righe)          │  + salva preprocessore e metriche
│ usa: pipeline.py     │
└────────┬─────────────┘
         │  3 modelli .joblib + JSON
         ▼
┌──────────────────────┐
│ predict.py           │  Inferenza su singolo paziente
│ (346 righe)          │  + top 5 fattori di rischio
│ usa: features.py     │
│ usa: pipeline.py     │
└────────┬─────────────┘
         │  PredictionResult (Pydantic)
         ▼
┌──────────────────────┐
│ seed_db.py           │  Genera 30 pazienti completi
│ (377 righe)          │  con predizioni + note cliniche
│ usa: predict.py      │
└────────┬─────────────┘
         │  synthetic_patients.json
         ▼
    ┌─────────────────────────────────┐
    │  MODULO 2: Backend API          │
    │  Importa PatientPredictor       │
    │  Legge synthetic_patients.json  │
    └─────────────────────────────────┘
```

---

## 4. Generatore Dati Sintetici

### File: `data/generate_synthea.py`

Genera 1000 pazienti sintetici **localizzati per il SSN italiano** in formato CSV compatibile Synthea. Non richiede Java.

### 4.1 Profili Clinici

Ogni paziente viene assegnato a uno di 6 profili clinici. Il profilo determina condizioni, farmaci, range dei parametri vitali e probabilità di complicanze.

| Profilo | Peso | Range Età | Condizioni Principali | Readmission % | Deterioration % |
|---------|------|-----------|----------------------|----------------|-----------------|
| **Cardiopatico** | 25% | 55-90 | Scompenso cardiaco, Ipertensione, FA | 30% | 10% |
| **BPCO** | 20% | 50-85 | BPCO, Asma, Ipertensione | 25% | 8% |
| **Diabetico** | 20% | 45-80 | Diabete T2, IRC, Ipertensione | 20% | 5% |
| **Nefropatico** | 15% | 50-85 | IRC, Ipertensione, Anemia | 35% | 12% |
| **Geriatrico** | 15% | 75-95 | Ipertensione, Diabete, Decadimento cognitivo | 30% | 15% |
| **Post-chirurgico** | 5% | 30-65 | Dolore cronico, Ipertensione | 10% | 3% |

### 4.2 Coerenza Clinica

I dati NON sono generati casualmente. Il generatore segue una logica clinica:

- Un **cardiopatico** avrà PA sistolica 130-175, prenderà Furosemide/Ramipril/Bisoprololo, avrà creatinina 1.0-2.5
- Un **nefropatico** avrà creatinina 2.0-5.0, emoglobina 8.0-12.0 (anemia), prenderà Eritropoietina
- Un **paziente BPCO** avrà SpO2 85-95% (bassa), prenderà Salbutamolo/Tiotropio

### 4.3 Localizzazione Italiana

- **Nomi**: generati con `Faker('it_IT')` — nomi e cognomi italiani reali
- **Codice Fiscale**: sintetico ma con struttura corretta (consonanti cognome + nome + data + comune)
- **Città**: Milano, Roma, Napoli, Torino, Bologna, Firenze, Palermo, Genova, Bari, Bergamo
- **Regioni**: Lombardia, Lazio, Campania, Piemonte, ecc.
- **Reparti**: Medicina Interna, Cardiologia, Pneumologia, Nefrologia, Geriatria
- **Farmaci**: nomi commerciali italiani (Furosemide, Ramipril, Metformina, ecc.)

### 4.4 Codifiche Standard

- **SNOMED-CT** per condizioni (es. 84114007 = Heart failure)
- **LOINC** per osservazioni (es. 8480-6 = Pressione sistolica)
- **ICD-10** nei metadati condizioni (es. I50.9 = Scompenso cardiaco)

### 4.5 Dati Generati per Paziente

| Tipo | Quantità per paziente | Dettaglio |
|------|----------------------|-----------|
| Encounters | 3-8 | 1 ricovero corrente + 0-4 precedenti + 1-3 visite ambulatoriali |
| Condizioni | 2-5 | Diagnosi attive con codice SNOMED |
| Farmaci | 3-6 | Prescrizioni attive con dosaggio |
| Osservazioni | 30-100+ | 3-8 set di vitali per encounter inpatient |
| Procedure | 1-3 | Procedure cliniche per profilo |
| Allergie | 0-1 | Allergie a farmaci (bassa probabilità) |

### 4.6 Riproducibilità

`random.seed(42)` e `np.random.seed(42)` garantiscono che ogni esecuzione produce gli stessi identici dati.

---

## 5. Feature Engineering

### File: `backend/ml/features.py`

Definisce l'intero schema delle feature e le funzioni di estrazione.

### 5.1 Le 26 Feature ML

#### Demografiche (2)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `age` | int | 30-95 | Età del paziente |
| `gender` | int | 0/1 | 0=Femmina, 1=Maschio |

#### Cliniche — Condizioni (7)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `n_active_conditions` | int | 0-6 | Numero totale comorbidità attive |
| `has_heart_failure` | int | 0/1 | Scompenso cardiaco (SNOMED 84114007) |
| `has_copd` | int | 0/1 | BPCO (SNOMED 13645005) |
| `has_chronic_kidney` | int | 0/1 | IRC (SNOMED 431855005) |
| `has_diabetes` | int | 0/1 | Diabete tipo 2 (SNOMED 44054006) |
| `has_hypertension` | int | 0/1 | Ipertensione (SNOMED 38341003) |
| `has_atrial_fibrillation` | int | 0/1 | FA (SNOMED 49436004) |

#### Cliniche — Farmaci e Procedure (2)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `n_active_medications` | int | 0-7 | Farmaci in corso |
| `n_recent_procedures` | int | 0-4 | Procedure negli ultimi 30 giorni |

#### Storiche (3)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `admissions_last_12m` | int | 0-4 | Ricoveri negli ultimi 12 mesi |
| `avg_los_previous` | float | 0-15 | Durata media degenze precedenti (giorni) |
| `days_since_last_admission` | float | 0-365 | Giorni dall'ultimo ricovero |

#### Parametri Vitali (8)

| Feature | Tipo | Range Normale | LOINC | Descrizione |
|---------|------|---------------|-------|-------------|
| `systolic_bp` | float | 90-140 | 8480-6 | Pressione arteriosa sistolica (mmHg) |
| `diastolic_bp` | float | 60-90 | 8462-4 | Pressione arteriosa diastolica (mmHg) |
| `heart_rate` | float | 60-100 | 8867-4 | Frequenza cardiaca (bpm) |
| `spo2` | float | 95-100 | 59408-5 | Saturazione ossigeno (%) |
| `temperature` | float | 36.0-37.5 | 8310-5 | Temperatura corporea (°C) |
| `glucose` | float | 70-140 | 2339-0 | Glicemia (mg/dL) |
| `creatinine` | float | 0.6-1.2 | 38483-4 | Creatinina (mg/dL) |
| `hemoglobin` | float | 12.0-17.0 | 718-7 | Emoglobina (g/dL) |

#### Temporali (2)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `admission_day_of_week` | int | 0-6 | 0=lunedì, 6=domenica |
| `admission_hour` | int | 0-23 | Ora del ricovero |

#### Lab (2)

| Feature | Tipo | Range | Descrizione |
|---------|------|-------|-------------|
| `days_since_last_lab` | float | 0-30 | Giorni dall'ultimo esame di laboratorio |
| `n_abnormal_labs` | int | 0-3 | Numero valori lab fuori range |

### 5.2 Target Variables (4)

| Target | Tipo | Range | Descrizione |
|--------|------|-------|-------------|
| `risk_score` | int | 1-99 | Score composito LACE+NEWS2 |
| `readmission_30d` | int | 0/1 | Riospedalizzazione entro 30 giorni |
| `los_days` | float | 0.5-15 | Durata degenza in giorni |
| `deterioration` | int | 0/1 | Deterioramento (TI o decesso) |

### 5.3 Modello Pydantic `PatientFeatures`

Tutte le feature sono validate tramite un modello Pydantic che funge sia da documentazione che da contratto:

```python
class PatientFeatures(BaseModel):
    patient_id: str
    encounter_id: str
    age: int
    gender: int
    n_active_conditions: int
    has_heart_failure: int
    # ... (tutte le 26 feature + 4 target opzionali)
```

### 5.4 Mappatura Feature → Nome Italiano

Il dizionario `FEATURE_DISPLAY_NAMES` mappa ogni feature tecnica al suo nome italiano per l'interfaccia utente:

```python
FEATURE_DISPLAY_NAMES = {
    'age': 'Età',
    'has_heart_failure': 'Scompenso cardiaco',
    'creatinine': 'Creatinina',
    'spo2': 'Saturazione ossigeno (SpO2)',
    # ...
}
```

---

## 6. Pipeline di Preprocessing

### File: `backend/ml/pipeline.py` + `data/preprocess.py`

### 6.1 Formula Risk Score (LACE + NEWS2)

Il risk score base è un composito pesato 0-100, calcolato con una formula deterministica ispirata al LACE Index e al NEWS2:

```
Score totale = Età + Comorbidità + Storia ricoveri + Vitali anomali + Polifarmacoterapia + Lab

Componenti:
┌─────────────────────────────────────────────────────────────────────┐
│ ETÀ (max 20 punti)                                                 │
│   punti = min(20, max(0, (età - 40) × 0.5))                       │
│   Es: 72 anni → (72-40)×0.5 = 16 punti                           │
├─────────────────────────────────────────────────────────────────────┤
│ COMORBIDITÀ — Charlson semplificato (max 25 punti)                 │
│   n_condizioni × 3                                                  │
│   + scompenso_cardiaco × 8                                          │
│   + BPCO × 6                                                        │
│   + IRC × 7                                                         │
│   + diabete × 4                                                     │
│   Es: 3 condizioni + scompenso → 3×3 + 8 = 17 punti              │
├─────────────────────────────────────────────────────────────────────┤
│ STORIA RICOVERI (max 20 punti)                                      │
│   ricoveri_12m × 7                                                   │
│   Es: 2 ricoveri → 2×7 = 14 punti                                 │
├─────────────────────────────────────────────────────────────────────┤
│ VITALI ANOMALI — NEWS2 inspired (max 20 punti)                     │
│   PA sistolica > 160 o < 90: +5                                    │
│   FC > 100 o < 50: +5                                               │
│   SpO2 < 94%: +5                                                    │
│   Temperatura > 38°C o < 36°C: +3                                  │
│   Creatinina > 1.5: +4                                              │
├─────────────────────────────────────────────────────────────────────┤
│ POLIFARMACOTERAPIA (max 10 punti)                                   │
│   max(0, (n_farmaci - 3) × 2)                                      │
│   Es: 5 farmaci → (5-3)×2 = 4 punti                               │
├─────────────────────────────────────────────────────────────────────┤
│ LAB MANCANTI (max 5 punti)                                          │
│   > 14 giorni senza lab: +5                                         │
│   > 7 giorni: +2                                                     │
└─────────────────────────────────────────────────────────────────────┘

Risultato: min(99, max(1, round(score)))
```

### 6.2 Classe `FeaturePreprocessor`

Wrapper serializzabile attorno a `StandardScaler` di sklearn:

```python
# In training:
preprocessor = FeaturePreprocessor()
X_scaled = preprocessor.fit_transform(df)
preprocessor.save('backend/ml/models/preprocessor.joblib')

# In inferenza:
preprocessor = FeaturePreprocessor.load('backend/ml/models/preprocessor.joblib')
X_scaled = preprocessor.transform_single(patient_features_dict)
```

Salva internamente:
- Lo scaler fittato
- La lista delle colonne feature
- Le medie per imputazione valori mancanti

### 6.3 Script `preprocess.py`

Workflow completo:

1. **Caricamento**: legge i 7 CSV da `data/synthea_output/`
2. **Filtro**: seleziona solo encounter di tipo `inpatient` (1 per paziente, il più recente)
3. **Estrazione**: per ogni encounter, chiama le 6 funzioni di estrazione da `features.py`
4. **Target**: calcola risk_score (formula), readmission_30d (simulato), los_days, deterioration
5. **Imputazione**: valori mancanti → mediana della colonna
6. **Validazione**: verifica assenza NaN, range corretti, stampa statistiche
7. **Output**: salva `data/processed/ml_dataset.csv`

### 6.4 Distribuzione Risultante

```
Risk Score:
  Basso  (1-25):     98 pazienti (9.8%)
  Medio  (26-50):   709 pazienti (70.9%)
  Alto   (51-75):   191 pazienti (19.1%)
  Critico (76-100):   2 pazienti (0.2%)

Readmission 30gg:  19.4% positivi
LOS media:          7.4 giorni
Età media:          69.6 anni
Distribuzione M/F:  49.7% / 50.3%
```

---

## 7. Training Modelli ML

### File: `backend/ml/train.py`

### 7.1 Split dei Dati

- **Train**: 800 campioni (80%)
- **Test**: 200 campioni (20%)
- Split **stratificato** per `readmission_30d` (mantiene le proporzioni della classe positiva)

### 7.2 I Tre Modelli

#### Modello 1: Risk Score Regressor

| Parametro | Valore |
|-----------|--------|
| Algoritmo | GradientBoostingRegressor (sklearn) / XGBRegressor |
| n_estimators | 200 |
| max_depth | 6 |
| learning_rate | 0.1 |
| subsample | 0.8 |
| Input | 26 feature |
| Output | Risk score 1-99 |
| **RMSE** | **3.45** |
| **MAE** | **2.67** |
| **R²** | **0.922** |

Il modello ML cattura il 92.2% della varianza del risk score base. In pratica, affina la formula LACE+NEWS2 con pattern non lineari.

#### Modello 2: Readmission Classifier

| Parametro | Valore |
|-----------|--------|
| Algoritmo | GradientBoostingClassifier / XGBClassifier |
| n_estimators | 200 |
| max_depth | 5 |
| scale_pos_weight | 3.0 (compensazione classe sbilanciata) |
| Input | 26 feature |
| Output | Probabilità 0.0-1.0 |
| **AUC-ROC** | **0.539** |
| **Precision** | **0.300** |
| **Recall** | **0.077** |
| **F1** | **0.122** |

L'AUC bassa è attesa: il target readmission è simulato con rumore casuale basato sul risk score. Con dati reali, le performance migliorerebbero significativamente.

#### Modello 3: Length of Stay Regressor

| Parametro | Valore |
|-----------|--------|
| Algoritmo | GradientBoostingRegressor / XGBRegressor |
| n_estimators | 150 |
| max_depth | 5 |
| Input | 26 feature |
| Output | Giorni di degenza (≥ 0.5) |
| **RMSE** | **2.44** |
| **MAE** | **1.64** |
| **R²** | **0.223** |

La LOS è difficile da predire perché dipende da molte variabili non catturate (risposta alla terapia, complicanze). L'errore medio di 1.64 giorni è accettabile per un prototipo.

### 7.3 Feature Importance

Le 10 feature più importanti (media aggregata sui 3 modelli):

| # | Feature | Nome Italiano | Importance |
|---|---------|--------------|------------|
| 1 | age | Età | 0.1346 |
| 2 | admission_day_of_week | Giorno della settimana ricovero | 0.1047 |
| 3 | creatinine | Creatinina | 0.0752 |
| 4 | days_since_last_admission | Giorni dall'ultimo ricovero | 0.0688 |
| 5 | spo2 | Saturazione ossigeno | 0.0651 |
| 6 | hemoglobin | Emoglobina | 0.0614 |
| 7 | has_heart_failure | Scompenso cardiaco | 0.0587 |
| 8 | n_active_conditions | Numero comorbidità | 0.0565 |
| 9 | systolic_bp | Pressione sistolica | 0.0526 |
| 10 | temperature | Temperatura corporea | 0.0507 |

### 7.4 Note su XGBoost vs sklearn

XGBoost richiede la libreria `libomp` su macOS (`brew install libomp`). Il codice include un **fallback automatico** su `sklearn.ensemble.GradientBoostingRegressor/Classifier` quando XGBoost non è disponibile. Le performance sono comparabili per il dataset di 1000 campioni.

---

## 8. Inferenza e Spiegabilità

### File: `backend/ml/predict.py`

### 8.1 Classe `PatientPredictor`

Classe singleton-like che carica i modelli una sola volta e li riutilizza:

```python
from backend.ml.predict import PatientPredictor

# Inizializzazione (carica modelli da disco)
predictor = PatientPredictor('backend/ml/models')

# Predizione su singolo paziente
result = predictor.predict({
    'patient_id': 'abc-123',
    'age': 72,
    'gender': 1,
    'n_active_conditions': 3,
    'has_heart_failure': 1,
    'systolic_bp': 155,
    'creatinine': 2.1,
    # ... tutte le 26 feature
})
```

### 8.2 Output: `PredictionResult`

```python
class PredictionResult(BaseModel):
    patient_id: str                     # ID paziente
    risk_score: int                     # 1-99
    risk_level: str                     # 'basso' | 'medio' | 'alto' | 'critico'
    readmission_probability: float      # 0.0 - 1.0
    readmission_label: str              # 'NELLA NORMA' | 'MONITORARE' | 'INTERVENTO URGENTE'
    predicted_los_days: float           # Giorni previsti
    risk_factors: list[RiskFactor]      # Top 5 fattori
    base_risk_score: int                # Score formula (senza ML)
    model_version: str                  # '1.0.0' o 'fallback'
```

### 8.3 Classificazione Rischio

| Risk Score | Livello | Colore UI | Azione suggerita |
|------------|---------|-----------|------------------|
| 1-25 | `basso` | Verde | Monitoraggio standard |
| 26-50 | `medio` | Giallo | Attenzione aumentata |
| 51-75 | `alto` | Arancione | Rivalutazione clinica |
| 76-99 | `critico` | Rosso | Intervento immediato |

| Readmission % | Label | Azione |
|---------------|-------|--------|
| < 30% | `NELLA NORMA` | Follow-up standard |
| 30-70% | `MONITORARE` | Piano di dimissione rafforzato |
| > 70% | `INTERVENTO URGENTE` | Rivalutazione terapia, consulenza |

### 8.4 Spiegabilità: Top 5 Fattori di Rischio

Per ogni predizione, il sistema restituisce i 5 fattori che più contribuiscono al risk score:

```python
class RiskFactor(BaseModel):
    factor: str          # "Scompenso cardiaco"
    feature_name: str    # "has_heart_failure"
    impact: str          # "alto" | "medio" | "basso"
    contribution: float  # 18.5
    value: float         # 1.0
    direction: str       # "aumenta_rischio" | "riduce_rischio"
```

Il contributo è calcolato come: `importance_modello × |valore_paziente - media_popolazione|`

**Esempio di output:**
```
Top fattori di rischio per Gianpietro Pacillo (score 76):
  1. Giorni dall'ultimo ricovero: alto (contributo 12.57) → riduce_rischio
  2. Pressione sistolica: alto (contributo 3.34) → aumenta_rischio
  3. Età: alto (contributo 2.11) → aumenta_rischio
  4. Frequenza cardiaca: alto (contributo 1.38) → aumenta_rischio
  5. Scompenso cardiaco: alto (contributo 0.59) → aumenta_rischio
```

### 8.5 Modalità Fallback

Se i modelli non sono disponibili (non ancora addestrati o file corrotti), il sistema degrada a una predizione basata solo sulla formula del risk score:

```python
result = PatientPredictor.create_fallback_prediction(patient_features)
# result.model_version == 'fallback'
# result.risk_factors == [] (nessuna spiegabilità senza modello)
```

---

## 9. Dati Demo

### File: `data/seed_db.py` → `data/sample/synthetic_patients.json`

### 9.1 Struttura JSON

Il file contiene 30 pazienti completi, selezionati con distribuzione stratificata:
- 8 ad alto rischio (score ≥ 60)
- 12 a rischio medio (score 35-60)
- 10 a basso rischio (score < 35)

### 9.2 Schema di un Paziente

```json
{
  "id": "uuid",
  "name": "Gianpietro Pacillo",
  "age": 85,
  "gender": "M",
  "fiscal_code": "PCLLGP41A01F205U",
  "department": "Medicina Interna",
  "admission_date": "2026-02-17T00:00:00",
  "is_active": true,

  "conditions": [
    { "icd10_code": "38341003", "description": "Hypertension", "is_active": true },
    { "icd10_code": "84114007", "description": "Heart failure", "is_active": true }
  ],

  "medications": [
    { "name": "Amlodipina", "dosage": "5mg", "frequency": "1x/die" },
    { "name": "Furosemide", "dosage": "25mg", "frequency": "1x/die" }
  ],

  "vitals": {
    "systolic_bp": 160, "diastolic_bp": 81,
    "heart_rate": 89, "spo2": 92.2,
    "temperature": 36.4, "glucose": 101,
    "creatinine": 2.39, "hemoglobin": 9.8
  },

  "prediction": {
    "risk_score": 76,
    "risk_level": "critico",
    "readmission_probability": 0.962,
    "readmission_label": "INTERVENTO URGENTE",
    "predicted_los_days": 6.2,
    "risk_factors": [
      { "factor": "Giorni dall'ultimo ricovero", "impact": "alto", "contribution": 12.57 },
      { "factor": "Pressione sistolica", "impact": "alto", "contribution": 3.34 }
    ]
  },

  "risk_trend": [
    { "date": "2026-02-13", "score": 70 },
    { "date": "2026-02-14", "score": 73 },
    { "date": "2026-02-20", "score": 76 }
  ],

  "encounters_history": [
    { "date": "2025-09-15", "department": "Medicina Interna", "los_days": 8, "type": "inpatient" }
  ],

  "clinical_notes": [
    {
      "author": "Dott. Rossi",
      "note_type": "admission",
      "content": "Paziente di 85 anni, maschio, giunge in PS per stato confusionale acuto...",
      "timestamp": "2026-02-18T00:00:00"
    }
  ]
}
```

### 9.3 Note Cliniche

Le note sono generate in italiano medico con template realistici:
- **Nota di ammissione**: motivo del ricovero, anamnesi, parametri all'ingresso
- **Note di decorso** (1-2): stato clinico, parametri, evoluzione
- **Consulenze**: specialistiche (cardio, nefro, ecc.)
- **Note di dimissione**: diagnosi, terapia, follow-up

Questo JSON è il **contratto di interfaccia** tra il Modulo 1 e i Moduli 2 (Backend API) e 3 (Frontend).

---

## 10. Guida Esecuzione

### Prerequisiti

```bash
python3 --version  # Python 3.11+
pip install pandas numpy scikit-learn faker joblib pydantic
# Opzionale per XGBoost:
brew install libomp && pip install xgboost
```

### Pipeline completa (da zero)

```bash
cd /Users/achillecolzani/Desktop/HEALTH\ GUARD/patientguard

# Step 1: Genera 1000 pazienti sintetici
python3 data/generate_synthea.py --num-patients 1000 --output-dir data/synthea_output

# Step 2: Preprocessa i CSV in dataset ML
python3 data/preprocess.py --input-dir data/synthea_output --output-dir data/processed

# Step 3: Addestra i 3 modelli
python3 -m backend.ml.train --data data/processed/ml_dataset.csv --output-dir backend/ml/models

# Step 4: Genera il JSON demo (30 pazienti)
python3 data/seed_db.py --mode json

# Step 5 (opzionale): Test inferenza
python3 -m backend.ml.predict
```

### Tempi di esecuzione

| Step | Tempo |
|------|-------|
| Generazione dati | ~15 secondi |
| Preprocessing | ~3 minuti |
| Training | ~30 secondi |
| Generazione JSON demo | ~10 secondi |
| **Totale** | **~4 minuti** |

---

## 11. Decisioni Architetturali

### 11.1 Python vs Synthea Java

**Scelta: generatore Python puro.**
- Java non è installato sulla macchina
- Synthea genera dati US-localized (nomi americani, stati USA)
- Il generatore Python produce CSV con schema identico a Synthea
- Pieno controllo sulla coerenza clinica e localizzazione italiana

### 11.2 XGBoost con fallback sklearn

**Scelta: XGBoost preferito, GradientBoosting come fallback.**
- XGBoost richiede `libomp` su macOS (non sempre installata)
- Il codice rileva automaticamente la disponibilità e usa sklearn se necessario
- Le performance sono comparabili su 1000 campioni
- Quando un membro del team ha homebrew, `brew install libomp` risolve

### 11.3 Readmission simulata

**Scelta: target readmission generato probabilisticamente dal risk score.**
- I dati sintetici non hanno vere riospedalizzazioni (gli encounter precedenti non cadono nella finestra di 30gg post-dimissione)
- Il target è generato con probabilità `0.05 + (risk_score/100) × 0.35`
- Questo produce un tasso realistico (~19%) e una correlazione sensata con il risk score

### 11.4 JSON come contratto di interfaccia

**Scelta: `synthetic_patients.json` invece del database.**
- Supabase non è ancora configurato (Modulo 2)
- Il JSON permette al team frontend di iniziare immediatamente
- Lo schema del JSON corrisponde esattamente allo schema del database SQL nella spec
- `seed_db.py --mode db` è predisposto come stub per il Modulo 2

### 11.5 Spiegabilità via Feature Importance

**Scelta: feature importance nativa + deviazione dalla media.**
- SHAP TreeExplainer era pianificato ma non incluso per evitare dipendenze aggiuntive
- Il metodo attuale (importance × |valore - media|) è semplice, veloce e sufficiente per la demo
- Può essere facilmente sostituito con SHAP nel Modulo 2 se necessario

---

## 12. Interfaccia con il Modulo 2

### 12.1 Cosa il Modulo 2 deve importare

```python
# In backend/routers/predictions.py (Modulo 2):
from backend.ml.predict import PatientPredictor, PredictionResult, RiskFactor
from backend.ml.features import FEATURE_DISPLAY_NAMES, ML_FEATURE_COLUMNS
from backend.ml.pipeline import compute_base_risk_score

# Inizializzazione al boot del server FastAPI:
predictor = PatientPredictor('backend/ml/models')

# Endpoint POST /api/v1/patients/{id}/predict:
result: PredictionResult = predictor.predict(patient_features_dict)
return result.model_dump()
```

### 12.2 Schema compatibile con il DB

Le chiavi del JSON demo corrispondono esattamente alle tabelle SQL nella spec:

| Chiave JSON | Tabella DB | Note |
|-------------|-----------|------|
| `id`, `name`, `age`, `gender`, `department` | `patients` | Diretto |
| `conditions[].icd10_code`, `.description` | `conditions` | Diretto |
| `medications[].name`, `.dosage` | `medications` | Diretto |
| `vitals.*` | `vitals` | Una riga per timestamp |
| `prediction.*` | `predictions` | `risk_factors` va in JSONB |
| `clinical_notes[]` | `clinical_notes` | Diretto |
| `encounters_history[]` | `encounters` | Diretto |

### 12.3 Per il seed del database

```python
# Quando Supabase è configurato (Modulo 2):
python3 data/seed_db.py --mode db
# Leggerà synthetic_patients.json e inserirà i dati nelle tabelle
```

### 12.4 Dipendenze da installare per il Modulo 2

Il `requirements.txt` è già completo. Per il Modulo 2 servono in più:
- `fastapi`, `uvicorn` — server API
- `supabase`, `psycopg2-binary` — connessione DB
- `httpx` — client HTTP
- `openai` — integrazione LLM (Modulo 5)
