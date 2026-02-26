"""
Modulo di feature engineering per PatientGuard.

Definisce le feature estratte dai dati Synthea e le funzioni di calcolo.
Ogni funzione prende dati grezzi (DataFrames Synthea) e restituisce
feature numeriche pronte per il modello ML.

Contiene anche:
- Costanti LOINC per mappatura osservazioni
- Costanti SNOMED per condizioni chiave
- Modello Pydantic PatientFeatures per validazione
- Mappatura feature -> nome italiano per la UI
"""

from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel


def _to_naive(ts: pd.Timestamp) -> pd.Timestamp:
    """Converte un timestamp in tz-naive (rimuove timezone info)."""
    if ts is None or pd.isna(ts):
        return ts
    if hasattr(ts, 'tz') and ts.tz is not None:
        return ts.tz_localize(None)
    return ts


def _parse_date_naive(value, errors='coerce') -> pd.Timestamp:
    """Parse una data/stringa in un Timestamp tz-naive."""
    ts = pd.to_datetime(value, errors=errors, utc=True)
    if ts is not None and not pd.isna(ts):
        return ts.tz_localize(None) if ts.tz is None else ts.tz_convert(None)
    return ts


# =============================================================================
# COSTANTI LOINC — codici per parametri vitali e lab
# =============================================================================

LOINC_CODES = {
    'systolic_bp': '8480-6',
    'diastolic_bp': '8462-4',
    'heart_rate': '8867-4',
    'spo2': '59408-5',
    'temperature': '8310-5',
    'glucose': '2339-0',
    'creatinine': '38483-4',
    'hemoglobin': '718-7',
}

# Mapping inverso: codice LOINC -> nome feature
LOINC_TO_FEATURE = {v: k for k, v in LOINC_CODES.items()}


# =============================================================================
# COSTANTI SNOMED — codici per condizioni cliniche chiave
# =============================================================================

SNOMED_CONDITIONS = {
    'heart_failure': '84114007',
    'copd': '13645005',
    'chronic_kidney': '431855005',
    'diabetes_type2': '44054006',
    'hypertension': '38341003',
    'atrial_fibrillation': '49436004',
    'coronary_artery_disease': '53741008',
    'anemia': '271737000',
}

# Mapping inverso
SNOMED_TO_CONDITION = {v: k for k, v in SNOMED_CONDITIONS.items()}


# =============================================================================
# RANGE NORMALI — per determinare valori anomali
# =============================================================================

NORMAL_RANGES = {
    'systolic_bp': (90, 140),
    'diastolic_bp': (60, 90),
    'heart_rate': (60, 100),
    'spo2': (95, 100),
    'temperature': (36.0, 37.5),
    'glucose': (70, 140),
    'creatinine': (0.6, 1.2),
    'hemoglobin': (12.0, 17.0),
}


# =============================================================================
# MODELLO PYDANTIC — schema feature per un singolo encounter
# =============================================================================

class PatientFeatures(BaseModel):
    """Schema completo delle feature per un singolo encounter."""

    # Identificativi
    patient_id: str
    encounter_id: str

    # Demografiche
    age: int
    gender: int  # 0=F, 1=M

    # Cliniche — condizioni
    n_active_conditions: int
    has_heart_failure: int
    has_copd: int
    has_chronic_kidney: int
    has_diabetes: int
    has_hypertension: int
    has_atrial_fibrillation: int

    # Cliniche — farmaci e procedure
    n_active_medications: int
    n_recent_procedures: int

    # Storiche
    admissions_last_12m: int
    avg_los_previous: float
    days_since_last_admission: float

    # Parametri vitali (ultime rilevazioni)
    systolic_bp: float
    diastolic_bp: float
    heart_rate: float
    spo2: float
    temperature: float
    glucose: float
    creatinine: float
    hemoglobin: float

    # Temporali
    admission_day_of_week: int  # 0=lunedì, 6=domenica
    admission_hour: int  # 0-23

    # Lab
    days_since_last_lab: float
    n_abnormal_labs: int

    # Target (calcolati in preprocessing, opzionali in fase di inferenza)
    risk_score: Optional[int] = None
    readmission_30d: Optional[int] = None
    los_days: Optional[float] = None
    deterioration: Optional[int] = None


# Lista delle feature usate dal modello ML (esclude ID e target)
ML_FEATURE_COLUMNS = [
    'age', 'gender',
    'n_active_conditions', 'has_heart_failure', 'has_copd',
    'has_chronic_kidney', 'has_diabetes', 'has_hypertension',
    'has_atrial_fibrillation',
    'n_active_medications', 'n_recent_procedures',
    'admissions_last_12m', 'avg_los_previous', 'days_since_last_admission',
    'systolic_bp', 'diastolic_bp', 'heart_rate', 'spo2',
    'temperature', 'glucose', 'creatinine', 'hemoglobin',
    'admission_day_of_week', 'admission_hour',
    'days_since_last_lab', 'n_abnormal_labs',
]

# Colonne target
TARGET_COLUMNS = ['risk_score', 'readmission_30d', 'los_days', 'deterioration']


# =============================================================================
# FUNZIONI DI ESTRAZIONE FEATURE
# =============================================================================

def extract_demographics(patients_df: pd.DataFrame,
                         patient_id: str,
                         reference_date: pd.Timestamp) -> dict:
    """
    Estrae età e sesso dal DataFrame pazienti.

    Returns:
        dict con chiavi 'age' e 'gender'
    """
    patient = patients_df[patients_df['Id'] == patient_id].iloc[0]

    # Calcolo età (normalizza timezone)
    birth_date = _parse_date_naive(patient['BirthDate'])
    ref = _to_naive(reference_date)
    age = int((ref - birth_date).days / 365.25)

    # Genere: 0=F, 1=M
    gender = 1 if patient['Gender'] == 'M' else 0

    return {'age': age, 'gender': gender}


def extract_clinical_features(conditions_df: pd.DataFrame,
                               medications_df: pd.DataFrame,
                               procedures_df: pd.DataFrame,
                               patient_id: str,
                               encounter_date: pd.Timestamp) -> dict:
    """
    Conta comorbidità attive, farmaci attivi e procedure recenti.

    Returns:
        dict con conteggi e flag per condizioni specifiche
    """
    encounter_date = _to_naive(encounter_date)

    # --- Condizioni attive alla data dell'encounter ---
    patient_conds = conditions_df[conditions_df['Patient'] == patient_id].copy()

    # Filtra condizioni attive (inizio prima dell'encounter, fine dopo o assente)
    patient_conds['Start'] = pd.to_datetime(patient_conds['Start'], errors='coerce', utc=True).dt.tz_localize(None)
    patient_conds['Stop'] = pd.to_datetime(patient_conds['Stop'], errors='coerce', utc=True).dt.tz_localize(None)

    active_mask = (
        (patient_conds['Start'] <= encounter_date) &
        (patient_conds['Stop'].isna() | (patient_conds['Stop'] >= encounter_date))
    )
    active_conds = patient_conds[active_mask]

    n_active_conditions = len(active_conds)

    # Flag per condizioni specifiche
    active_codes = set(active_conds['Code'].astype(str).values)
    condition_flags = {}
    for key, snomed_code in SNOMED_CONDITIONS.items():
        flag_name = f'has_{key}' if not key.startswith('has_') else key
        # Normalizza il nome
        if key == 'diabetes_type2':
            flag_name = 'has_diabetes'
        elif key == 'coronary_artery_disease':
            continue  # Non è una feature del modello
        elif key == 'anemia':
            continue  # Non è una feature del modello
        else:
            flag_name = f'has_{key}'
        condition_flags[flag_name] = 1 if snomed_code in active_codes else 0

    # --- Farmaci attivi ---
    patient_meds = medications_df[medications_df['Patient'] == patient_id].copy()
    patient_meds['Start'] = pd.to_datetime(patient_meds['Start'], errors='coerce', utc=True).dt.tz_localize(None)
    patient_meds['Stop'] = pd.to_datetime(patient_meds['Stop'], errors='coerce', utc=True).dt.tz_localize(None)

    active_meds_mask = (
        (patient_meds['Start'] <= encounter_date) &
        (patient_meds['Stop'].isna() | (patient_meds['Stop'] >= encounter_date))
    )
    n_active_medications = int(active_meds_mask.sum())

    # --- Procedure recenti (ultimi 30 giorni) ---
    patient_procs = procedures_df[procedures_df['Patient'] == patient_id].copy()
    patient_procs['Start'] = pd.to_datetime(patient_procs['Start'], errors='coerce', utc=True).dt.tz_localize(None)
    recent_procs_mask = (
        (patient_procs['Start'] >= encounter_date - pd.Timedelta(days=30)) &
        (patient_procs['Start'] <= encounter_date)
    )
    n_recent_procedures = int(recent_procs_mask.sum())

    result = {
        'n_active_conditions': n_active_conditions,
        'n_active_medications': n_active_medications,
        'n_recent_procedures': n_recent_procedures,
    }
    result.update(condition_flags)

    return result


def extract_historical_features(encounters_df: pd.DataFrame,
                                 patient_id: str,
                                 current_encounter_id: str,
                                 current_encounter_date: pd.Timestamp) -> dict:
    """
    Calcola metriche storiche: ricoveri ultimi 12 mesi,
    durata media degenze precedenti, giorni dall'ultimo ricovero.

    Returns:
        dict con chiavi storiche
    """
    current_encounter_date = _to_naive(current_encounter_date)

    patient_enc = encounters_df[
        (encounters_df['Patient'] == patient_id) &
        (encounters_df['Id'] != current_encounter_id)
    ].copy()

    patient_enc['Start'] = pd.to_datetime(patient_enc['Start'], errors='coerce', utc=True).dt.tz_localize(None)
    patient_enc['Stop'] = pd.to_datetime(patient_enc['Stop'], errors='coerce', utc=True).dt.tz_localize(None)

    # Solo ricoveri inpatient
    inpatient = patient_enc[patient_enc['EncounterClass'] == 'inpatient']

    # Ricoveri negli ultimi 12 mesi
    twelve_months_ago = current_encounter_date - pd.Timedelta(days=365)
    recent_admissions = inpatient[inpatient['Start'] >= twelve_months_ago]
    admissions_last_12m = len(recent_admissions)

    # Durata media delle degenze precedenti
    if len(inpatient) > 0 and inpatient['Stop'].notna().any():
        completed = inpatient[inpatient['Stop'].notna()]
        los_values = (completed['Stop'] - completed['Start']).dt.total_seconds() / 86400
        avg_los_previous = float(los_values.mean()) if len(los_values) > 0 else 0.0
    else:
        avg_los_previous = 0.0

    # Giorni dall'ultimo ricovero
    if len(inpatient) > 0:
        last_admission = inpatient['Start'].max()
        days_since = (current_encounter_date - last_admission).total_seconds() / 86400
        days_since_last_admission = max(0, float(days_since))
    else:
        days_since_last_admission = 365.0  # Nessun ricovero precedente

    return {
        'admissions_last_12m': admissions_last_12m,
        'avg_los_previous': round(avg_los_previous, 1),
        'days_since_last_admission': round(days_since_last_admission, 1),
    }


def extract_vital_signs(observations_df: pd.DataFrame,
                         patient_id: str,
                         encounter_id: str) -> dict:
    """
    Estrae gli ultimi parametri vitali dall'encounter.
    Se un parametro non è presente, usa un valore mediano di default.

    Returns:
        dict con i valori dei parametri vitali
    """
    # Filtra osservazioni dell'encounter
    enc_obs = observations_df[
        (observations_df['Patient'] == patient_id) &
        (observations_df['Encounter'] == encounter_id)
    ].copy()

    enc_obs['Date'] = pd.to_datetime(enc_obs['Date'], errors='coerce', utc=True).dt.tz_localize(None)
    enc_obs['Value'] = pd.to_numeric(enc_obs['Value'], errors='coerce')

    # Valori di default (mediane popolazionali)
    defaults = {
        'systolic_bp': 120.0,
        'diastolic_bp': 75.0,
        'heart_rate': 75.0,
        'spo2': 97.0,
        'temperature': 36.6,
        'glucose': 100.0,
        'creatinine': 1.0,
        'hemoglobin': 13.0,
    }

    vitals = {}
    for feature_name, loinc_code in LOINC_CODES.items():
        obs_for_code = enc_obs[enc_obs['Code'] == loinc_code]
        if len(obs_for_code) > 0:
            # Prendi l'osservazione più recente
            latest = obs_for_code.sort_values('Date', ascending=False).iloc[0]
            value = latest['Value']
            if pd.notna(value):
                vitals[feature_name] = float(value)
            else:
                vitals[feature_name] = defaults[feature_name]
        else:
            vitals[feature_name] = defaults[feature_name]

    return vitals


def extract_temporal_features(encounter_start: pd.Timestamp) -> dict:
    """
    Estrae features temporali dal timestamp dell'encounter.

    Returns:
        dict con giorno della settimana (0-6) e ora (0-23)
    """
    return {
        'admission_day_of_week': encounter_start.dayofweek,
        'admission_hour': encounter_start.hour,
    }


def extract_lab_features(observations_df: pd.DataFrame,
                          patient_id: str,
                          encounter_date: pd.Timestamp) -> dict:
    """
    Calcola giorni dall'ultimo esame lab e numero di valori anomali.

    Returns:
        dict con days_since_last_lab e n_abnormal_labs
    """
    # Filtra osservazioni lab del paziente
    lab_obs = observations_df[
        (observations_df['Patient'] == patient_id) &
        (observations_df['Category'] == 'laboratory')
    ].copy()

    encounter_date = _to_naive(encounter_date)
    lab_obs['Date'] = pd.to_datetime(lab_obs['Date'], errors='coerce', utc=True).dt.tz_localize(None)
    lab_obs['Value'] = pd.to_numeric(lab_obs['Value'], errors='coerce')

    if len(lab_obs) == 0:
        return {
            'days_since_last_lab': 30.0,
            'n_abnormal_labs': 0,
        }

    # Giorni dall'ultimo lab
    last_lab_date = lab_obs['Date'].max()
    days_since = (encounter_date - last_lab_date).total_seconds() / 86400
    days_since_last_lab = max(0, float(days_since))

    # Conta valori anomali (ultime osservazioni)
    n_abnormal = 0
    lab_codes = {
        'glucose': '2339-0',
        'creatinine': '38483-4',
        'hemoglobin': '718-7',
    }

    for feature_name, code in lab_codes.items():
        code_obs = lab_obs[lab_obs['Code'] == code]
        if len(code_obs) > 0:
            latest_value = code_obs.sort_values('Date', ascending=False).iloc[0]['Value']
            if pd.notna(latest_value):
                low, high = NORMAL_RANGES[feature_name]
                if latest_value < low or latest_value > high:
                    n_abnormal += 1

    return {
        'days_since_last_lab': round(days_since_last_lab, 1),
        'n_abnormal_labs': n_abnormal,
    }


# =============================================================================
# MAPPATURA FEATURE -> NOME ITALIANO (per UI e spiegabilità)
# =============================================================================

FEATURE_DISPLAY_NAMES = {
    'age': 'Età',
    'gender': 'Sesso',
    'n_active_conditions': 'Numero comorbidità',
    'has_heart_failure': 'Scompenso cardiaco',
    'has_copd': 'BPCO',
    'has_chronic_kidney': 'Insufficienza renale cronica',
    'has_diabetes': 'Diabete',
    'has_hypertension': 'Ipertensione',
    'has_atrial_fibrillation': 'Fibrillazione atriale',
    'n_active_medications': 'Numero farmaci attivi',
    'n_recent_procedures': 'Procedure recenti',
    'admissions_last_12m': 'Ricoveri ultimi 12 mesi',
    'avg_los_previous': 'Durata media degenze precedenti',
    'days_since_last_admission': 'Giorni dall\'ultimo ricovero',
    'systolic_bp': 'Pressione sistolica',
    'diastolic_bp': 'Pressione diastolica',
    'heart_rate': 'Frequenza cardiaca',
    'spo2': 'Saturazione ossigeno (SpO2)',
    'temperature': 'Temperatura corporea',
    'glucose': 'Glicemia',
    'creatinine': 'Creatinina',
    'hemoglobin': 'Emoglobina',
    'admission_day_of_week': 'Giorno della settimana ricovero',
    'admission_hour': 'Ora del ricovero',
    'days_since_last_lab': 'Giorni dall\'ultimo esame lab',
    'n_abnormal_labs': 'Esami lab anomali',
}
