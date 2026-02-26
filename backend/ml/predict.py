"""
Pipeline di inferenza per PatientGuard.

Carica i modelli addestrati e genera predizioni con spiegabilità.

Uso standalone:
    cd patientguard
    python3 -m backend.ml.predict

Uso in API (Module 2):
    from backend.ml.predict import PatientPredictor
    predictor = PatientPredictor()
    result = predictor.predict(patient_features_dict)
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from pydantic import BaseModel

# Aggiungi root al path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.features import FEATURE_DISPLAY_NAMES, ML_FEATURE_COLUMNS
from ml.pipeline import FeaturePreprocessor, compute_base_risk_score


# =============================================================================
# MODELLI PYDANTIC PER OUTPUT
# =============================================================================

class RiskFactor(BaseModel):
    """Singolo fattore di rischio per la spiegazione della predizione."""
    factor: str          # Nome leggibile in italiano
    feature_name: str    # Nome tecnico della feature
    impact: str          # 'alto', 'medio', 'basso'
    contribution: float  # Contributo numerico alla predizione
    value: float         # Valore attuale della feature per il paziente
    direction: str       # 'aumenta_rischio' o 'riduce_rischio'


class PredictionResult(BaseModel):
    """Risultato completo di una predizione per un paziente."""
    patient_id: str
    risk_score: int                    # 0-100
    risk_level: str                    # 'basso', 'medio', 'alto', 'critico'
    readmission_probability: float     # 0.0-1.0
    readmission_label: str             # 'NELLA NORMA', 'MONITORARE', 'INTERVENTO URGENTE'
    predicted_los_days: float          # Giorni di degenza previsti
    risk_factors: list[RiskFactor]     # Top 5 fattori di rischio
    base_risk_score: int               # Score formula base (pre-ML)
    model_version: str                 # Versione del modello


# =============================================================================
# PREDICTOR
# =============================================================================

MODEL_VERSION = '1.0.0'


class PatientPredictor:
    """
    Classe principale per le predizioni.
    Carica i modelli una sola volta e li riutilizza per più predizioni.

    Esempio:
        predictor = PatientPredictor('backend/ml/models')
        result = predictor.predict({
            'patient_id': '123',
            'age': 72,
            'gender': 1,
            'n_active_conditions': 3,
            ...
        })
    """

    def __init__(self, models_dir: str = 'backend/ml/models'):
        self.models_dir = Path(models_dir)
        self.risk_model = None
        self.readmission_model = None
        self.los_model = None
        self.preprocessor: Optional[FeaturePreprocessor] = None
        self.feature_importance: Optional[dict] = None
        self._loaded = False

        self._load_models()

    def _load_models(self) -> None:
        """Carica tutti i modelli e il preprocessore da disco."""
        try:
            self.risk_model = joblib.load(self.models_dir / 'risk_score_model.joblib')
            self.readmission_model = joblib.load(self.models_dir / 'readmission_model.joblib')
            self.los_model = joblib.load(self.models_dir / 'los_model.joblib')
            self.preprocessor = FeaturePreprocessor.load(
                str(self.models_dir / 'preprocessor.joblib')
            )

            fi_path = self.models_dir / 'feature_importance.json'
            if fi_path.exists():
                with open(fi_path, 'r', encoding='utf-8') as f:
                    self.feature_importance = json.load(f)

            self._loaded = True
            print(f"Modelli caricati da {self.models_dir}/")

        except FileNotFoundError as e:
            print(f"Attenzione: modelli non trovati in {self.models_dir}/. "
                  f"Uso predizione fallback. Errore: {e}")
            self._loaded = False

    def predict(self, patient_features: dict) -> PredictionResult:
        """
        Genera predizione completa per un paziente.

        Args:
            patient_features: dizionario con tutte le feature del paziente.
                              Deve contenere almeno le chiavi in ML_FEATURE_COLUMNS
                              più 'patient_id'.

        Returns:
            PredictionResult con score, probabilità e spiegazione
        """
        patient_id = patient_features.get('patient_id', 'unknown')

        # Calcola risk score base (formula)
        base_risk_score = compute_base_risk_score(patient_features)

        if not self._loaded:
            return self.create_fallback_prediction(patient_features)

        # Preprocessa feature per i modelli
        X = self.preprocessor.transform_single(patient_features)

        # --- Risk Score ML ---
        risk_score_raw = float(self.risk_model.predict(X)[0])
        risk_score = int(np.clip(round(risk_score_raw), 1, 99))

        # --- Readmission ---
        readmission_prob = float(self.readmission_model.predict_proba(X)[0][1])

        # --- Length of Stay ---
        los_raw = float(self.los_model.predict(X)[0])
        predicted_los = max(0.5, round(los_raw, 1))

        # --- Spiegabilità ---
        risk_factors = self._explain_prediction(X, patient_features)

        return PredictionResult(
            patient_id=patient_id,
            risk_score=risk_score,
            risk_level=self._classify_risk_level(risk_score),
            readmission_probability=round(readmission_prob, 4),
            readmission_label=self._classify_readmission(readmission_prob),
            predicted_los_days=predicted_los,
            risk_factors=risk_factors,
            base_risk_score=base_risk_score,
            model_version=MODEL_VERSION,
        )

    def _explain_prediction(self, X: np.ndarray,
                             patient_features: dict) -> list[RiskFactor]:
        """
        Calcola i top 5 fattori che contribuiscono al risk score.

        Usa feature importance del modello risk_score come proxy.
        Per ogni feature, il contributo è proporzionale a:
        - importance del modello × valore normalizzato della feature
        """
        if self.feature_importance is None:
            return []

        factors = []
        feature_columns = self.preprocessor.feature_columns

        # Calcola contributo per ogni feature
        for feature_name in feature_columns:
            fi_data = self.feature_importance.get(feature_name)
            if fi_data is None:
                continue

            importance = fi_data.get('overall', 0)
            display_name = fi_data.get('display_name', feature_name)

            # Valore attuale del paziente
            value = float(patient_features.get(feature_name, 0))

            # Contributo = importance × abs(valore normalizzato)
            mean = self.preprocessor.feature_means_.get(feature_name, 0)
            deviation = abs(value - mean)
            contribution = importance * deviation

            # Determina direzione
            if value > mean:
                direction = 'aumenta_rischio'
            else:
                direction = 'riduce_rischio'

            # Per le feature binarie (has_*), il contributo è più semplice
            if feature_name.startswith('has_') and value == 1:
                direction = 'aumenta_rischio'
                contribution = importance * 10

            factors.append({
                'feature_name': feature_name,
                'display_name': display_name,
                'importance': importance,
                'contribution': contribution,
                'value': value,
                'direction': direction,
            })

        # Ordina per contributo e prendi top 5
        factors.sort(key=lambda x: x['contribution'], reverse=True)
        top_factors = factors[:5]

        # Classifica impatto
        risk_factors = []
        for f in top_factors:
            if f['contribution'] > 0.5:
                impact = 'alto'
            elif f['contribution'] > 0.2:
                impact = 'medio'
            else:
                impact = 'basso'

            risk_factors.append(RiskFactor(
                factor=f['display_name'],
                feature_name=f['feature_name'],
                impact=impact,
                contribution=round(f['contribution'], 2),
                value=f['value'],
                direction=f['direction'],
            ))

        return risk_factors

    @staticmethod
    def _classify_risk_level(score: int) -> str:
        """
        Classifica il livello di rischio.
        0-25: basso (verde), 26-50: medio (giallo),
        51-75: alto (arancione), 76-100: critico (rosso)
        """
        if score <= 25:
            return 'basso'
        elif score <= 50:
            return 'medio'
        elif score <= 75:
            return 'alto'
        else:
            return 'critico'

    @staticmethod
    def _classify_readmission(prob: float) -> str:
        """
        Etichetta per rischio riospedalizzazione.
        < 30%: NELLA NORMA, 30-70%: MONITORARE, > 70%: INTERVENTO URGENTE
        """
        if prob < 0.3:
            return 'NELLA NORMA'
        elif prob <= 0.7:
            return 'MONITORARE'
        else:
            return 'INTERVENTO URGENTE'

    @staticmethod
    def create_fallback_prediction(patient_features: dict) -> PredictionResult:
        """
        Predizione di fallback quando i modelli ML non sono disponibili.
        Usa solo la formula base del risk score.
        """
        patient_id = patient_features.get('patient_id', 'unknown')
        base_score = compute_base_risk_score(patient_features)

        # Stima readmission dalla formula
        readmission_prob = min(0.95, max(0.05, base_score / 200 + 0.05))

        # Stima LOS dalla formula
        predicted_los = max(1.0, base_score / 10)

        return PredictionResult(
            patient_id=patient_id,
            risk_score=base_score,
            risk_level=PatientPredictor._classify_risk_level(base_score),
            readmission_probability=round(readmission_prob, 4),
            readmission_label=PatientPredictor._classify_readmission(readmission_prob),
            predicted_los_days=round(predicted_los, 1),
            risk_factors=[],
            base_risk_score=base_score,
            model_version='fallback',
        )


# =============================================================================
# TEST STANDALONE
# =============================================================================

if __name__ == '__main__':
    import pandas as pd

    print("=== PatientGuard — Test Inferenza ===\n")

    # Carica predictor
    predictor = PatientPredictor('backend/ml/models')

    # Carica un campione dal dataset
    df = pd.read_csv('data/processed/ml_dataset.csv')
    sample = df.iloc[0]

    # Converti in dizionario
    features = sample.to_dict()

    # Predici
    result = predictor.predict(features)

    print(f"Paziente: {result.patient_id}")
    print(f"Risk Score: {result.risk_score}/100 ({result.risk_level})")
    print(f"  Score base (formula): {result.base_risk_score}")
    print(f"Riospedalizzazione 30gg: {result.readmission_probability*100:.1f}% ({result.readmission_label})")
    print(f"Degenza prevista: {result.predicted_los_days} giorni")
    print(f"Modello: v{result.model_version}")

    print(f"\nTop fattori di rischio:")
    for rf in result.risk_factors:
        print(f"  - {rf.factor}: impatto {rf.impact}, contributo {rf.contribution:.2f} "
              f"(valore: {rf.value}, {rf.direction})")

    # Test su più pazienti
    print(f"\n--- Test su 5 pazienti ---")
    for i in range(min(5, len(df))):
        features = df.iloc[i].to_dict()
        result = predictor.predict(features)
        dept = features.get('department', '?')
        print(f"  [{dept}] Score: {result.risk_score:3d} ({result.risk_level:8s}) | "
              f"Readmission: {result.readmission_probability*100:5.1f}% | "
              f"LOS: {result.predicted_los_days:4.1f}gg | "
              f"Top factor: {result.risk_factors[0].factor if result.risk_factors else 'N/A'}")
