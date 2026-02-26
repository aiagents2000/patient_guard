"""
Router predizioni ML.

Endpoints:
    POST /api/v1/patients/{id}/predict — Trigger nuova predizione ML
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.models.database import DataStore, get_datastore
from backend.models.schemas import PredictionResponse
from backend.ml.predict import PatientPredictor
from backend.services.alert_service import generate_alerts_for_prediction

router = APIRouter(prefix="/api/v1/patients", tags=["predictions"])

# Singleton predictor — caricato una volta alla prima richiesta
_predictor: PatientPredictor | None = None


def get_predictor() -> PatientPredictor:
    global _predictor
    if _predictor is None:
        from backend.config import get_settings
        settings = get_settings()
        _predictor = PatientPredictor(settings.ml_models_dir)
    return _predictor


@router.post("/{patient_id}/predict", response_model=PredictionResponse)
async def predict_patient(
    patient_id: str,
    store: DataStore = Depends(get_datastore),
    predictor: PatientPredictor = Depends(get_predictor),
):
    """
    Esegue una nuova predizione ML per il paziente.

    1. Recupera le feature del paziente dal DB/JSON
    2. Esegue la predizione con i 3 modelli XGBoost
    3. Salva il risultato
    4. Genera eventuali alert
    5. Restituisce la predizione completa
    """
    # Verifica che il paziente esista
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Recupera feature ML
    features = await store.get_patient_features(patient_id)
    if not features:
        raise HTTPException(status_code=422, detail="Feature ML non disponibili per il paziente")

    # Recupera score precedente per alert di variazione
    prev_predictions = await store.get_patient_predictions(patient_id, limit=1)
    previous_score = prev_predictions[-1].get('risk_score') if prev_predictions else None

    # Esegui predizione
    result = predictor.predict(features)

    # Costruisci dizionario predizione
    prediction_dict = {
        'risk_score': result.risk_score,
        'risk_level': result.risk_level,
        'readmission_probability': result.readmission_probability,
        'readmission_label': result.readmission_label,
        'predicted_los_days': result.predicted_los_days,
        'risk_factors': [
            {
                'factor': rf.factor,
                'impact': rf.impact,
                'contribution': rf.contribution,
            }
            for rf in result.risk_factors
        ],
        'base_risk_score': result.base_risk_score,
        'model_version': result.model_version,
    }

    # Salva predizione
    await store.save_prediction(patient_id, prediction_dict)

    # Genera alert se necessario
    vitals = patient.get('vitals', {})
    await generate_alerts_for_prediction(
        store=store,
        patient_id=patient_id,
        patient_name=patient.get('name', ''),
        prediction=prediction_dict,
        vitals=vitals,
        previous_score=previous_score,
    )

    return prediction_dict
