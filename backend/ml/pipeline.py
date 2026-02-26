"""
Pipeline di preprocessing riutilizzabile per PatientGuard.

Usata sia in data/preprocess.py (training) che in backend/ml/predict.py (inference).
Contiene:
- Formula risk score composito (LACE Index + NEWS2)
- Funzioni di calcolo target variables
- FeaturePreprocessor: classe serializzabile per scaling delle feature
"""

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ml.features import ML_FEATURE_COLUMNS, _to_naive


# =============================================================================
# FORMULA RISK SCORE — ispirata a LACE Index + NEWS2
# =============================================================================

def compute_base_risk_score(features: dict) -> int:
    """
    Calcola il risk score composito 0-100 basato su fattori clinici.

    Ispirato a:
    - LACE Index (Length of stay, Acuity, Comorbidities, ED visits)
    - NEWS2 (National Early Warning Score)
    - HOSPITAL Score

    Componenti:
    - Età: max 20 punti
    - Comorbidità (Charlson semplificato): max 25 punti
    - Storia ricoveri: max 20 punti
    - Parametri vitali anomali: max 20 punti
    - Polifarmacoterapia: max 10 punti
    - Lab mancanti: max 5 punti

    Args:
        features: dizionario con le feature del paziente

    Returns:
        Score intero tra 1 e 99
    """
    score = 0.0

    # --- Età (max 20 punti) ---
    age = features.get('age', 50)
    score += min(20, max(0, (age - 40) * 0.5))

    # --- Comorbidità — Charlson Comorbidity Index semplificato (max 25 punti) ---
    n_conditions = features.get('n_active_conditions', 0)
    has_chf = features.get('has_heart_failure', 0)
    has_copd = features.get('has_copd', 0)
    has_ckd = features.get('has_chronic_kidney', 0)
    has_diabetes = features.get('has_diabetes', 0)

    comorbidity_score = (
        n_conditions * 3 +
        has_chf * 8 +
        has_copd * 6 +
        has_ckd * 7 +
        has_diabetes * 4
    )
    score += min(25, comorbidity_score)

    # --- Storia ricoveri (max 20 punti) ---
    admissions_12m = features.get('admissions_last_12m', 0)
    score += min(20, admissions_12m * 7)

    # --- Parametri vitali anomali — NEWS2-inspired (max 20 punti) ---
    vitals_score = 0

    systolic_bp = features.get('systolic_bp', 120)
    if systolic_bp > 160 or systolic_bp < 90:
        vitals_score += 5

    heart_rate = features.get('heart_rate', 75)
    if heart_rate > 100 or heart_rate < 50:
        vitals_score += 5

    spo2 = features.get('spo2', 97)
    if spo2 < 94:
        vitals_score += 5

    temperature = features.get('temperature', 36.6)
    if temperature > 38.0 or temperature < 36.0:
        vitals_score += 3

    creatinine = features.get('creatinine', 1.0)
    if creatinine > 1.5:
        vitals_score += 4

    score += min(20, vitals_score)

    # --- Polifarmacoterapia (max 10 punti) ---
    n_meds = features.get('n_active_medications', 0)
    score += min(10, max(0, (n_meds - 3) * 2))

    # --- Lab recenti mancanti (max 5 punti) ---
    days_since_last_lab = features.get('days_since_last_lab', 0)
    if days_since_last_lab > 14:
        score += 5
    elif days_since_last_lab > 7:
        score += 2

    return min(99, max(1, int(round(score))))


# =============================================================================
# CALCOLO TARGET VARIABLES
# =============================================================================

def compute_los_days(encounter_start: pd.Timestamp,
                     encounter_stop: Optional[pd.Timestamp]) -> Optional[float]:
    """
    Calcola la durata della degenza in giorni.

    Returns:
        Numero di giorni (float) o None se il paziente non è ancora dimesso
    """
    if encounter_stop is None or pd.isna(encounter_stop):
        return None

    los = (encounter_stop - encounter_start).total_seconds() / 86400
    return max(0.5, round(los, 1))  # Minimo mezzo giorno


def compute_readmission_30d(encounters_df: pd.DataFrame,
                             patient_id: str,
                             discharge_date: pd.Timestamp) -> int:
    """
    Verifica se il paziente è stato riospedalizzato entro 30 giorni dalla dimissione.

    Returns:
        1 se riospedalizzato entro 30gg, 0 altrimenti
    """
    if pd.isna(discharge_date):
        return 0

    future_enc = encounters_df[
        (encounters_df['Patient'] == patient_id) &
        (encounters_df['EncounterClass'] == 'inpatient')
    ].copy()

    discharge_date = _to_naive(discharge_date)
    future_enc['Start'] = pd.to_datetime(future_enc['Start'], errors='coerce', utc=True).dt.tz_localize(None)

    # Cerca ricoveri entro 30 giorni dalla dimissione
    window_start = discharge_date
    window_end = discharge_date + pd.Timedelta(days=30)

    readmissions = future_enc[
        (future_enc['Start'] > window_start) &
        (future_enc['Start'] <= window_end)
    ]

    return 1 if len(readmissions) > 0 else 0


def compute_deterioration(encounters_df: pd.DataFrame,
                           encounter_id: str,
                           patient_id: str,
                           patients_df: Optional[pd.DataFrame] = None) -> int:
    """
    Determina se c'è stato deterioramento durante il ricovero:
    - Decesso durante il ricovero
    - Trasferimento in terapia intensiva (simulato tramite encounter successivo ravvicinato)

    Returns:
        1 se deterioramento, 0 altrimenti
    """
    # Controlla decesso
    if patients_df is not None:
        patient = patients_df[patients_df['Id'] == patient_id]
        if len(patient) > 0:
            death_date = patient.iloc[0].get('DeathDate', '')
            if death_date and str(death_date) != '' and str(death_date) != 'nan':
                return 1

    # Controlla se c'è stato un encounter di emergenza subito dopo
    enc = encounters_df[encounters_df['Id'] == encounter_id]
    if len(enc) == 0:
        return 0

    enc_stop_raw = enc.iloc[0].get('Stop', None)
    if not enc_stop_raw or str(enc_stop_raw).strip() == '':
        return 0
    enc_stop = pd.to_datetime(enc_stop_raw, errors='coerce', utc=True)
    if pd.isna(enc_stop):
        return 0
    enc_stop = _to_naive(enc_stop)

    # Cerca encounter emergency entro 2 giorni dalla dimissione
    emergency_enc = encounters_df[
        (encounters_df['Patient'] == patient_id) &
        (encounters_df['EncounterClass'] == 'emergency')
    ].copy()
    emergency_enc['Start'] = pd.to_datetime(emergency_enc['Start'], errors='coerce', utc=True).dt.tz_localize(None)

    within_2days = emergency_enc[
        (emergency_enc['Start'] > enc_stop) &
        (emergency_enc['Start'] <= enc_stop + pd.Timedelta(days=2))
    ]

    return 1 if len(within_2days) > 0 else 0


# =============================================================================
# FEATURE PREPROCESSOR — serializzabile per riuso in inferenza
# =============================================================================

class FeaturePreprocessor:
    """
    Preprocessore che gestisce scaling e selezione feature.
    Salvabile con joblib per riutilizzo in fase di inferenza.

    Uso in training:
        preprocessor = FeaturePreprocessor()
        X_scaled = preprocessor.fit_transform(df)
        preprocessor.save('backend/ml/models/preprocessor.joblib')

    Uso in inferenza:
        preprocessor = FeaturePreprocessor.load('backend/ml/models/preprocessor.joblib')
        X_scaled = preprocessor.transform(df)
    """

    def __init__(self, feature_columns: Optional[list[str]] = None):
        self.scaler = StandardScaler()
        self.feature_columns = feature_columns or ML_FEATURE_COLUMNS
        self.is_fitted = False
        self.feature_means_: Optional[dict] = None

    def fit(self, df: pd.DataFrame) -> 'FeaturePreprocessor':
        """Fitta lo scaler sulle feature numeriche."""
        X = df[self.feature_columns].values.astype(np.float64)
        self.scaler.fit(X)
        self.is_fitted = True

        # Salva le medie per imputazione valori mancanti in inferenza
        self.feature_means_ = {
            col: float(df[col].mean()) for col in self.feature_columns
        }

        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Trasforma le feature applicando lo scaling."""
        if not self.is_fitted:
            raise RuntimeError("Il preprocessore non è stato fittato. Chiama fit() prima.")

        X = df[self.feature_columns].copy()

        # Imputa valori mancanti con le medie del training set
        if self.feature_means_:
            for col in self.feature_columns:
                if col in X.columns and X[col].isna().any():
                    X[col] = X[col].fillna(self.feature_means_[col])

        return self.scaler.transform(X.values.astype(np.float64))

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit + transform in un passo."""
        self.fit(df)
        return self.transform(df)

    def save(self, path: str) -> None:
        """Salva il preprocessore con joblib."""
        data = {
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'is_fitted': self.is_fitted,
            'feature_means': self.feature_means_,
        }
        joblib.dump(data, path)
        print(f"Preprocessore salvato in {path}")

    @classmethod
    def load(cls, path: str) -> 'FeaturePreprocessor':
        """Carica il preprocessore salvato."""
        data = joblib.load(path)
        preprocessor = cls(feature_columns=data['feature_columns'])
        preprocessor.scaler = data['scaler']
        preprocessor.is_fitted = data['is_fitted']
        preprocessor.feature_means_ = data['feature_means']
        return preprocessor

    def transform_single(self, features: dict) -> np.ndarray:
        """
        Trasforma un singolo record (dizionario) in array pronto per il modello.
        Utile per inferenza su singolo paziente.
        """
        if not self.is_fitted:
            raise RuntimeError("Il preprocessore non è stato fittato.")

        values = []
        for col in self.feature_columns:
            val = features.get(col)
            if val is None and self.feature_means_:
                val = self.feature_means_.get(col, 0.0)
            values.append(float(val) if val is not None else 0.0)

        X = np.array([values], dtype=np.float64)
        return self.scaler.transform(X)
