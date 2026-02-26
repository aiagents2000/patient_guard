"""
Servizio LLM per generare riassunti clinici in italiano.

Supporta OpenAI e Anthropic. Se nessun provider è configurato,
genera un riassunto strutturato basato sulle regole.
"""

from datetime import datetime
from typing import Optional

from backend.config import get_settings


SYSTEM_PROMPT = """Sei un assistente medico AI che lavora nel SSN italiano.
Il tuo compito è generare un riassunto clinico conciso e strutturato
della cartella di un paziente, utile al medico di reparto per una rapida
comprensione dello stato del paziente.

Scrivi SEMPRE in italiano. Usa terminologia medica appropriata.
Struttura il riassunto in queste sezioni:
1. QUADRO CLINICO: diagnosi principale e comorbidità
2. PARAMETRI ATTUALI: vitali e lab rilevanti
3. RISCHIO: score AI, fattori principali, livello
4. RACCOMANDAZIONI: suggerimenti basati sui dati

Sii conciso (max 300 parole)."""


async def generate_summary(
    patient: dict,
    record: dict,
    prediction: dict,
) -> dict:
    """
    Genera un riassunto LLM della cartella clinica.

    Returns:
        dict con 'summary', 'generated_at', 'model'
    """
    settings = get_settings()

    # Costruisci il prompt con i dati del paziente
    user_prompt = _build_patient_prompt(patient, record, prediction)

    if settings.openai_api_key:
        summary, model = await _call_openai(user_prompt, settings.openai_api_key)
    elif settings.anthropic_api_key:
        summary, model = await _call_anthropic(user_prompt, settings.anthropic_api_key)
    else:
        summary = _generate_rule_based_summary(patient, record, prediction)
        model = "rule-based"

    return {
        'patient_id': patient.get('id', ''),
        'summary': summary,
        'generated_at': datetime.now().isoformat(),
        'model': model,
    }


def _build_patient_prompt(patient: dict, record: dict, prediction: dict) -> str:
    """Costruisce il prompt con i dati del paziente per l'LLM."""
    name = patient.get('name', 'Paziente')
    age = patient.get('age', 0)
    gender = 'M' if patient.get('gender') == 'M' else 'F'
    dept = patient.get('department', '')

    # Condizioni
    conditions = record.get('conditions', [])
    cond_text = ', '.join(c.get('description', '') for c in conditions[:5])

    # Farmaci
    meds = record.get('medications', [])
    med_text = ', '.join(f"{m.get('name', '')} {m.get('dosage', '')}" for m in meds[:6])

    # Vitali
    vitals = record.get('vitals', {})
    if isinstance(vitals, list):
        vitals = vitals[0] if vitals else {}

    # Predizione
    pred = prediction
    risk_score = pred.get('risk_score', 0)
    risk_level = pred.get('risk_level', '')
    readm = pred.get('readmission_probability', 0)
    los = pred.get('predicted_los_days', 0)
    factors = pred.get('risk_factors', [])
    factors_text = ', '.join(f.get('factor', '') for f in factors[:3])

    # Note cliniche
    notes = record.get('clinical_notes', [])
    notes_text = ''
    for n in notes[:2]:
        notes_text += f"\n- [{n.get('note_type', '')}] {n.get('content', '')[:200]}"

    return f"""Paziente: {name}, {age} anni, sesso {gender}
Reparto: {dept}
Diagnosi: {cond_text or 'nessuna nota'}
Terapia: {med_text or 'nessuna'}
Parametri vitali: PA {vitals.get('systolic_bp', '?')}/{vitals.get('diastolic_bp', '?')}, FC {vitals.get('heart_rate', '?')}, SpO2 {vitals.get('spo2', '?')}%, T {vitals.get('temperature', '?')}°C
Lab: Creatinina {vitals.get('creatinine', '?')}, Hb {vitals.get('hemoglobin', '?')}, Glicemia {vitals.get('glucose', '?')}
Risk Score AI: {risk_score}/100 ({risk_level})
Probabilità riospedalizzazione 30gg: {readm*100:.0f}%
Degenza prevista: {los} giorni
Fattori di rischio principali: {factors_text or 'N/A'}
Note cliniche recenti:{notes_text or ' nessuna'}

Genera un riassunto clinico strutturato."""


async def _call_openai(prompt: str, api_key: str) -> tuple[str, str]:
    """Chiama OpenAI GPT per il riassunto."""
    import openai

    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content, "gpt-4o-mini"


async def _call_anthropic(prompt: str, api_key: str) -> tuple[str, str]:
    """Chiama Anthropic Claude per il riassunto."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        data = response.json()
        text = data.get("content", [{}])[0].get("text", "Errore nella generazione.")
        return text, "claude-haiku-4-5-20251001"


def _generate_rule_based_summary(patient: dict, record: dict, prediction: dict) -> str:
    """Genera un riassunto strutturato senza LLM, basato su regole."""
    name = patient.get('name', 'Paziente')
    age = patient.get('age', 0)
    gender = 'maschio' if patient.get('gender') == 'M' else 'femmina'
    dept = patient.get('department', '')

    conditions = record.get('conditions', [])
    meds = record.get('medications', [])
    vitals = record.get('vitals', {})
    if isinstance(vitals, list):
        vitals = vitals[0] if vitals else {}

    risk_score = prediction.get('risk_score', 0)
    risk_level = prediction.get('risk_level', 'N/A')
    readm = prediction.get('readmission_probability', 0)
    los = prediction.get('predicted_los_days', 0)
    factors = prediction.get('risk_factors', [])

    # Sezione 1: Quadro clinico
    cond_list = [c.get('description', '') for c in conditions[:5] if c.get('description')]
    cond_text = ', '.join(cond_list) if cond_list else 'nessuna patologia documentata'

    # Sezione 2: Parametri
    sbp = vitals.get('systolic_bp', '?')
    dbp = vitals.get('diastolic_bp', '?')
    hr = vitals.get('heart_rate', '?')
    spo2 = vitals.get('spo2', '?')
    temp = vitals.get('temperature', '?')

    # Sezione 3: Rischio
    level_text = {
        'basso': 'BASSO — nessun intervento urgente necessario',
        'medio': 'MEDIO — monitoraggio attento raccomandato',
        'alto': 'ALTO — valutazione clinica prioritaria',
        'critico': 'CRITICO — intervento immediato raccomandato',
    }
    risk_text = level_text.get(risk_level, f'{risk_level}')
    factors_text = '; '.join(f"{f.get('factor', '')}: impatto {f.get('impact', '')}"
                              for f in factors[:3])

    # Sezione 4: Raccomandazioni
    recs = []
    if risk_level in ('alto', 'critico'):
        recs.append("Rivalutazione clinica urgente")
    if readm > 0.5:
        recs.append("Pianificare dimissione protetta con follow-up ravvicinato")
    if vitals.get('spo2', 100) < 92:
        recs.append("Monitoraggio continuo della saturazione, considerare O2 terapia")
    if vitals.get('creatinine', 0) > 2.0:
        recs.append("Controllo funzionalità renale, idratazione, eventuale consulenza nefrologica")
    if not recs:
        recs.append("Proseguire monitoraggio standard e terapia in corso")

    summary = f"""**QUADRO CLINICO**
{name}, {age} anni, {gender}, ricoverato in {dept}.
Diagnosi: {cond_text}.
Terapia in corso: {', '.join(m.get('name', '') for m in meds[:4]) or 'nessuna'}.

**PARAMETRI ATTUALI**
PA {sbp}/{dbp} mmHg, FC {hr} bpm, SpO2 {spo2}%, T {temp}°C.
Creatinina: {vitals.get('creatinine', '?')} mg/dL, Hb: {vitals.get('hemoglobin', '?')} g/dL, Glicemia: {vitals.get('glucose', '?')} mg/dL.

**RISCHIO AI**
Risk Score: {risk_score}/100 — {risk_text}.
Probabilità riospedalizzazione 30gg: {readm*100:.0f}%.
Degenza prevista: {los} giorni.
Fattori principali: {factors_text or 'N/A'}.

**RACCOMANDAZIONI**
{chr(10).join('- ' + r for r in recs)}"""

    return summary
