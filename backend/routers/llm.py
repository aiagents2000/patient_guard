"""
Router LLM — riassunto clinico AI.

Endpoints:
    GET /api/v1/patients/{id}/summary — Riassunto LLM della cartella
"""

from fastapi import APIRouter, Depends, HTTPException

from models.database import DataStore, get_datastore
from models.schemas import LLMSummaryResponse
from services.llm_service import generate_summary

router = APIRouter(prefix="/api/v1/patients", tags=["llm"])


@router.get("/{patient_id}/summary", response_model=LLMSummaryResponse)
async def get_patient_summary(
    patient_id: str,
    store: DataStore = Depends(get_datastore),
):
    """
    Genera un riassunto clinico del paziente tramite LLM.

    Se nessun provider LLM è configurato, usa un riassunto
    strutturato basato su regole.
    """
    patient = await store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    record = await store.get_patient_record(patient_id)
    if not record:
        raise HTTPException(status_code=404, detail="Cartella clinica non trovata")

    prediction = patient.get('prediction', {})

    result = await generate_summary(patient, record, prediction)
    return result
