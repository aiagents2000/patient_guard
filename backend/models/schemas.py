"""
Pydantic models per le risposte API di PatientGuard.

Questi schemi definiscono il contratto tra backend e frontend.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# VITALI
# =============================================================================

class VitalsResponse(BaseModel):
    timestamp: Optional[str] = None
    systolic_bp: int = 120
    diastolic_bp: int = 75
    heart_rate: int = 75
    spo2: float = 97.0
    temperature: float = 36.6
    glucose: int = 100
    creatinine: float = 1.0
    hemoglobin: float = 13.0


# =============================================================================
# CONDIZIONI E FARMACI
# =============================================================================

class ConditionResponse(BaseModel):
    icd10_code: str = ""
    description: str
    is_active: bool = True
    onset_date: Optional[str] = None


class MedicationResponse(BaseModel):
    name: str
    dosage: str = ""
    frequency: str = ""
    is_active: bool = True


# =============================================================================
# PREDIZIONI
# =============================================================================

class RiskFactorResponse(BaseModel):
    factor: str
    impact: str  # 'alto', 'medio', 'basso'
    contribution: float


class PredictionResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: str  # 'basso', 'medio', 'alto', 'critico'
    readmission_probability: float = Field(ge=0.0, le=1.0)
    readmission_label: str
    predicted_los_days: float
    risk_factors: list[RiskFactorResponse] = []
    base_risk_score: Optional[int] = None
    model_version: str = "1.0.0"


class PredictionHistoryItem(BaseModel):
    date: Optional[str] = None
    risk_score: int
    model_version: str = "1.0.0"
    created_at: Optional[str] = None


# =============================================================================
# NOTE CLINICHE
# =============================================================================

class ClinicalNoteResponse(BaseModel):
    author: str = ""
    note_type: str  # 'admission', 'progress', 'discharge', 'consultation'
    content: str
    timestamp: Optional[str] = None


# =============================================================================
# ENCOUNTER STORICO
# =============================================================================

class EncounterHistoryResponse(BaseModel):
    date: Optional[str] = None
    department: str = ""
    los_days: int = 0
    type: str = "inpatient"


# =============================================================================
# PAZIENTE
# =============================================================================

class PatientSummary(BaseModel):
    """Riepilogo paziente per la lista."""
    id: str
    name: str
    age: int
    gender: str
    department: str
    admission_date: Optional[str] = None
    is_active: bool = True
    risk_score: int = 0
    risk_level: str = "basso"
    readmission_probability: float = 0.0
    readmission_label: str = "NELLA NORMA"


class PatientDetail(BaseModel):
    """Dettaglio completo paziente."""
    id: str
    name: str
    age: int
    gender: str
    fiscal_code: str = ""
    department: str
    admission_date: Optional[str] = None
    is_active: bool = True
    conditions: list[ConditionResponse] = []
    medications: list[MedicationResponse] = []
    vitals: VitalsResponse = VitalsResponse()
    prediction: PredictionResponse
    risk_trend: list[dict] = []
    encounters_history: list[EncounterHistoryResponse] = []
    clinical_notes: list[ClinicalNoteResponse] = []


class PatientRecord(BaseModel):
    """Cartella clinica completa."""
    conditions: list[ConditionResponse] = []
    medications: list[MedicationResponse] = []
    vitals: VitalsResponse = VitalsResponse()
    clinical_notes: list[ClinicalNoteResponse] = []
    encounters_history: list[EncounterHistoryResponse] = []


# =============================================================================
# ALERT
# =============================================================================

class AlertResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str = ""
    alert_type: str  # 'critical_vitals', 'risk_increase', 'readmission_warning', 'lab_critical'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    is_read: bool = False
    is_resolved: bool = False
    created_at: Optional[str] = None


class AlertCreate(BaseModel):
    patient_id: str
    alert_type: str
    severity: str
    message: str


# =============================================================================
# STATISTICHE
# =============================================================================

class RiskDistribution(BaseModel):
    basso: int = 0
    medio: int = 0
    alto: int = 0
    critico: int = 0


class StatsOverview(BaseModel):
    total_patients: int
    active_patients: int
    avg_risk_score: float
    risk_distribution: RiskDistribution
    active_alerts: int


class DepartmentStats(BaseModel):
    department: str
    patient_count: int
    avg_risk_score: float
    critical_count: int = 0
    high_count: int = 0


# =============================================================================
# LLM
# =============================================================================

class LLMSummaryResponse(BaseModel):
    patient_id: str
    summary: str
    generated_at: str
    model: str = ""
