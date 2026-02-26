"""
Router pazienti — CRUD e filtri.

Endpoints:
    GET  /api/v1/patients          — Lista pazienti con filtri
    GET  /api/v1/patients/{id}     — Dettaglio paziente completo
    GET  /api/v1/patients/{id}/vitals      — Parametri vitali
    GET  /api/v1/patients/{id}/predictions — Storico predizioni
    GET  /api/v1/patients/{id}/record      — Cartella clinica completa
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.models.database import DataStore, get_datastore
from backend.models.schemas import (
    PatientDetail,
    PatientRecord,
    PatientSummary,
    PredictionHistoryItem,
    VitalsResponse,
)

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def _patient_to_summary(p: dict) -> dict:
    """Converte un record paziente raw in PatientSummary."""
    pred = p.get('prediction', {})
    return {
        'id': p.get('id', ''),
        'name': p.get('name', ''),
        'age': p.get('age', 0),
        'gender': p.get('gender', ''),
        'department': p.get('department', ''),
        'admission_date': p.get('admission_date'),
        'is_active': p.get('is_active', True),
        'risk_score': pred.get('risk_score', 0),
        'risk_level': pred.get('risk_level', 'basso'),
        'readmission_probability': pred.get('readmission_probability', 0),
        'readmission_label': pred.get('readmission_label', 'NELLA NORMA'),
    }


@router.get("", response_model=list[PatientSummary])
async def list_patients(
    department: Optional[str] = Query(None, description="Filtra per reparto"),
    risk_level: Optional[str] = Query(None, description="Filtra per livello rischio"),
    search: Optional[str] = Query(None, description="Cerca per nome o codice fiscale"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    store: DataStore = Depends(get_datastore),
):
    """Lista pazienti con filtri opzionali."""
    patients = await store.get_patients(
        department=department,
        risk_level=risk_level,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [_patient_to_summary(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientDetail)
async def get_patient(
    patient_id: str,
    store: DataStore = Depends(get_datastore),
):
    """Dettaglio completo di un paziente."""
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return patient


@router.get("/{patient_id}/vitals", response_model=list[VitalsResponse])
async def get_patient_vitals(
    patient_id: str,
    limit: int = Query(50, ge=1, le=500),
    store: DataStore = Depends(get_datastore),
):
    """Serie temporale parametri vitali."""
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return await store.get_patient_vitals(patient_id, limit=limit)


@router.get("/{patient_id}/predictions", response_model=list[PredictionHistoryItem])
async def get_patient_predictions(
    patient_id: str,
    limit: int = Query(30, ge=1, le=100),
    store: DataStore = Depends(get_datastore),
):
    """Storico predizioni per trend chart."""
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return await store.get_patient_predictions(patient_id, limit=limit)


@router.get("/{patient_id}/record", response_model=PatientRecord)
async def get_patient_record(
    patient_id: str,
    store: DataStore = Depends(get_datastore),
):
    """Cartella clinica completa (condizioni, farmaci, lab, note, encounter)."""
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    record = await store.get_patient_record(patient_id)
    if not record:
        raise HTTPException(status_code=404, detail="Cartella clinica non trovata")
    return record
