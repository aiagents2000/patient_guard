"""
Servizio alert per PatientGuard.

Genera automaticamente alert basati su:
1. Parametri vitali critici
2. Aumento risk score > 15 punti in 24h
3. Probabilità riospedalizzazione > 70%
4. Valori lab critici
"""

from backend.models.database import DataStore


# Soglie parametri vitali critici
VITAL_THRESHOLDS = {
    'systolic_bp_high': 180,
    'systolic_bp_low': 80,
    'heart_rate_high': 120,
    'heart_rate_low': 40,
    'spo2_low': 90,
    'temperature_high': 39.0,
    'glucose_high': 300,
    'glucose_low': 50,
}

# Soglie lab critiche
LAB_THRESHOLDS = {
    'creatinine_high': 3.0,
    'hemoglobin_low': 7.0,
}


def check_vitals_alerts(vitals: dict, patient_id: str, patient_name: str) -> list[dict]:
    """Controlla i parametri vitali e genera alert se critici."""
    alerts = []
    critical_msgs = []

    sbp = vitals.get('systolic_bp', 0)
    if sbp > VITAL_THRESHOLDS['systolic_bp_high']:
        critical_msgs.append(f"PA sistolica {sbp} mmHg (ipertensione critica)")
    elif sbp < VITAL_THRESHOLDS['systolic_bp_low'] and sbp > 0:
        critical_msgs.append(f"PA sistolica {sbp} mmHg (ipotensione)")

    hr = vitals.get('heart_rate', 0)
    if hr > VITAL_THRESHOLDS['heart_rate_high']:
        critical_msgs.append(f"FC {hr} bpm (tachicardia)")
    elif hr < VITAL_THRESHOLDS['heart_rate_low'] and hr > 0:
        critical_msgs.append(f"FC {hr} bpm (bradicardia)")

    spo2 = vitals.get('spo2', 100)
    if spo2 < VITAL_THRESHOLDS['spo2_low']:
        critical_msgs.append(f"SpO2 {spo2}% (desaturazione)")

    temp = vitals.get('temperature', 36.6)
    if temp > VITAL_THRESHOLDS['temperature_high']:
        critical_msgs.append(f"Temperatura {temp}°C (iperpiressia)")

    gluc = vitals.get('glucose', 100)
    if gluc > VITAL_THRESHOLDS['glucose_high']:
        critical_msgs.append(f"Glicemia {gluc} mg/dL (iperglicemia critica)")
    elif gluc < VITAL_THRESHOLDS['glucose_low'] and gluc > 0:
        critical_msgs.append(f"Glicemia {gluc} mg/dL (ipoglicemia)")

    if critical_msgs:
        alerts.append({
            'patient_id': patient_id,
            'patient_name': patient_name,
            'alert_type': 'critical_vitals',
            'severity': 'critical',
            'message': f"Parametri vitali critici: {', '.join(critical_msgs)}",
        })

    # Lab critici
    lab_msgs = []
    creat = vitals.get('creatinine', 1.0)
    if creat > LAB_THRESHOLDS['creatinine_high']:
        lab_msgs.append(f"Creatinina {creat} mg/dL")

    hb = vitals.get('hemoglobin', 13.0)
    if hb < LAB_THRESHOLDS['hemoglobin_low'] and hb > 0:
        lab_msgs.append(f"Emoglobina {hb} g/dL")

    if lab_msgs:
        alerts.append({
            'patient_id': patient_id,
            'patient_name': patient_name,
            'alert_type': 'lab_critical',
            'severity': 'high',
            'message': f"Valori lab critici: {', '.join(lab_msgs)}",
        })

    return alerts


def check_prediction_alerts(
    prediction: dict,
    patient_id: str,
    patient_name: str,
    previous_score: int | None = None,
) -> list[dict]:
    """Genera alert basati sui risultati della predizione ML."""
    alerts = []

    risk_score = prediction.get('risk_score', 0)
    readmission_prob = prediction.get('readmission_probability', 0)

    # Aumento risk score > 15 punti
    if previous_score is not None and (risk_score - previous_score) > 15:
        alerts.append({
            'patient_id': patient_id,
            'patient_name': patient_name,
            'alert_type': 'risk_increase',
            'severity': 'high',
            'message': (f"Risk score aumentato di {risk_score - previous_score} punti "
                        f"({previous_score} → {risk_score}). Rivalutare il paziente."),
        })

    # Readmission > 70%
    if readmission_prob > 0.7:
        alerts.append({
            'patient_id': patient_id,
            'patient_name': patient_name,
            'alert_type': 'readmission_warning',
            'severity': 'high' if readmission_prob < 0.85 else 'critical',
            'message': (f"Probabilità riospedalizzazione {readmission_prob*100:.0f}%. "
                        f"Considerare piano di dimissione protetta."),
        })

    return alerts


async def generate_alerts_for_prediction(
    store: DataStore,
    patient_id: str,
    patient_name: str,
    prediction: dict,
    vitals: dict | None = None,
    previous_score: int | None = None,
) -> list[dict]:
    """
    Genera e salva tutti gli alert per una nuova predizione.
    Chiamata dal router predictions dopo ogni predict.
    """
    new_alerts = []

    # Alert da predizione
    new_alerts.extend(check_prediction_alerts(
        prediction, patient_id, patient_name, previous_score
    ))

    # Alert da vitali (se forniti)
    if vitals:
        new_alerts.extend(check_vitals_alerts(vitals, patient_id, patient_name))

    # Salva in DB
    saved = []
    for alert_data in new_alerts:
        saved_alert = await store.create_alert(alert_data)
        saved.append(saved_alert)

    return saved
