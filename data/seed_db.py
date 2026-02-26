"""
Genera dati di esempio per il database e il file JSON demo.

Fase 1 (Modulo 1): Genera data/sample/synthetic_patients.json
    con ~30 pazienti completi (dati + predizioni) per la demo frontend.

Fase 2 (Modulo 2): Inserisce i dati in Supabase PostgreSQL (stub).

Uso:
    cd patientguard
    python3 data/seed_db.py --mode json
    python3 data/seed_db.py --mode db    # richiede Modulo 2
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from backend.ml.predict import PatientPredictor

# Seed per riproducibilità
random.seed(42)
np.random.seed(42)

# Data di riferimento
REFERENCE_DATE = datetime(2026, 2, 20)

# Template note cliniche in italiano
NOTE_TEMPLATES = {
    'admission': [
        "Paziente di {age} anni, {gender_text}, giunge in PS per {motivo}. "
        "Anamnesi positiva per {condizioni}. In terapia con {farmaci}. "
        "All'ingresso PA {pa} mmHg, FC {fc} bpm, SpO2 {spo2}%, T {temp}°C. "
        "Si dispone ricovero in {reparto} per monitoraggio e terapia.",

        "Ricovero programmato per {motivo}. Paziente noto per {condizioni}. "
        "Parametri all'ingresso stabili: PA {pa} mmHg, FC {fc} bpm, SpO2 {spo2}%. "
        "Terapia domiciliare: {farmaci}. Si programma iter diagnostico.",
    ],
    'progress': [
        "In {giornata} giornata di degenza. Paziente clinicamente {stato}. "
        "PA {pa} mmHg, FC {fc} bpm, SpO2 {spo2}%. {note_aggiuntive} "
        "Si prosegue terapia in corso.",

        "Decorso clinico {stato}. Parametri vitali: PA {pa}, FC {fc}, "
        "SpO2 {spo2}%. Esami ematochimici: creatinina {creatinina}, "
        "Hb {hb}. {note_aggiuntive}",
    ],
    'consultation': [
        "Consulenza {specialita}: valutato il paziente per {motivo_consulenza}. "
        "Si consiglia {consiglio}. Controllo tra {giorni} giorni.",
    ],
    'discharge': [
        "Dimissione in {giornata} giornata. Diagnosi di dimissione: {diagnosi}. "
        "Terapia alla dimissione: {farmaci}. "
        "Controllo ambulatoriale tra {giorni} giorni. "
        "Istruzioni: {istruzioni}.",
    ],
}

MOTIVI_RICOVERO = {
    'cardiopatico': ['dispnea ingravescente', 'scompenso cardiaco acuto', 'dolore toracico atipico', 'fibrillazione atriale ad alta risposta'],
    'bpco': ['riacutizzazione BPCO', 'insufficienza respiratoria acuta', 'polmonite comunitaria'],
    'diabetico': ['iperglicemia sintomatica', 'piede diabetico', 'scompenso metabolico'],
    'nefropatico': ['peggioramento funzionalità renale', 'sovraccarico idrico', 'iperkaliemia'],
    'geriatrico': ['caduta accidentale', 'stato confusionale acuto', 'infezione delle vie urinarie', 'anemia sintomatica'],
    'post_chirurgico': ['intervento chirurgico programmato', 'colecistectomia', 'ernia inguinale'],
}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carica i dati processati e i CSV originali."""
    ml_dataset = pd.read_csv('data/processed/ml_dataset.csv')
    patients = pd.read_csv('data/synthea_output/patients.csv')
    conditions = pd.read_csv('data/synthea_output/conditions.csv')
    medications = pd.read_csv('data/synthea_output/medications.csv')
    return ml_dataset, patients, conditions, medications


def generate_clinical_notes(patient_data: dict) -> list[dict]:
    """Genera note cliniche realistiche in italiano per un paziente."""
    notes = []
    age = patient_data['age']
    gender_text = 'maschio' if patient_data.get('gender', 1) == 1 else 'femmina'
    department = patient_data.get('department', 'Medicina Interna')

    # Determina il profilo per il motivo di ricovero
    profile = 'geriatrico'
    for cond in patient_data.get('conditions', []):
        desc_lower = cond.get('description', '').lower()
        if 'heart failure' in desc_lower:
            profile = 'cardiopatico'
            break
        elif 'copd' in desc_lower:
            profile = 'bpco'
            break
        elif 'diabetes' in desc_lower:
            profile = 'diabetico'
            break
        elif 'kidney' in desc_lower:
            profile = 'nefropatico'
            break

    motivi = MOTIVI_RICOVERO.get(profile, MOTIVI_RICOVERO['geriatrico'])
    condizioni_text = ', '.join([c['description'] for c in patient_data.get('conditions', [])[:3]])
    farmaci_text = ', '.join([m['name'] for m in patient_data.get('medications', [])[:3]])

    vitals = patient_data.get('vitals', {})
    pa = f"{vitals.get('systolic_bp', 120)}/{vitals.get('diastolic_bp', 75)}"

    # Nota di ammissione
    template = random.choice(NOTE_TEMPLATES['admission'])
    notes.append({
        'author': f'Dott. {random.choice(["Rossi", "Bianchi", "Colombo", "Russo", "Ferrari"])}',
        'note_type': 'admission',
        'content': template.format(
            age=age, gender_text=gender_text,
            motivo=random.choice(motivi),
            condizioni=condizioni_text or 'nessuna comorbidità nota',
            farmaci=farmaci_text or 'nessuna terapia domiciliare',
            pa=pa, fc=vitals.get('heart_rate', 75),
            spo2=vitals.get('spo2', 97), temp=vitals.get('temperature', 36.6),
            reparto=department
        ),
        'timestamp': (REFERENCE_DATE - timedelta(days=random.randint(1, 5))).isoformat(),
    })

    # Note di decorso (1-2)
    for i in range(random.randint(1, 2)):
        stato = random.choice(['stabile', 'in miglioramento', 'stazionario', 'lievemente migliorato'])
        note_aggiuntive = random.choice([
            'Diuresi valida.', 'Apiretico.', 'Alvo regolare.',
            'Riferisce lieve miglioramento della dispnea.',
            'Persistente astenia.', 'Alimentazione regolare.',
        ])
        template = random.choice(NOTE_TEMPLATES['progress'])
        notes.append({
            'author': f'Dott. {random.choice(["Verdi", "Neri", "Moretti", "Conti", "Ricci"])}',
            'note_type': 'progress',
            'content': template.format(
                giornata=random.choice(['seconda', 'terza', 'quarta']),
                stato=stato, pa=pa,
                fc=vitals.get('heart_rate', 75),
                spo2=vitals.get('spo2', 97),
                creatinina=vitals.get('creatinine', 1.0),
                hb=vitals.get('hemoglobin', 13.0),
                note_aggiuntive=note_aggiuntive
            ),
            'timestamp': (REFERENCE_DATE - timedelta(days=random.randint(0, 2))).isoformat(),
        })

    return notes


def build_patient_record(row: pd.Series, patients_df: pd.DataFrame,
                          conditions_df: pd.DataFrame,
                          medications_df: pd.DataFrame,
                          predictor: PatientPredictor) -> dict:
    """Costruisce un record paziente completo per il JSON demo."""
    patient_id = row['patient_id']

    # Dati demografici
    patient_info = patients_df[patients_df['Id'] == patient_id]
    if len(patient_info) > 0:
        p = patient_info.iloc[0]
        name = f"{p['First']} {p['Last']}"
        fiscal_code = str(p.get('SSN', ''))
    else:
        name = 'Paziente Sconosciuto'
        fiscal_code = ''

    gender_char = 'M' if row['gender'] == 1 else 'F'
    department = row.get('department', 'Medicina Interna')

    # Condizioni del paziente
    patient_conds = conditions_df[conditions_df['Patient'] == patient_id]
    conditions_list = []
    for _, cond in patient_conds.iterrows():
        conditions_list.append({
            'icd10_code': str(cond.get('Code', '')),
            'description': str(cond.get('Description', '')),
            'is_active': str(cond.get('Stop', '')) == '' or pd.isna(cond.get('Stop', '')),
        })

    # Farmaci del paziente
    patient_meds = medications_df[medications_df['Patient'] == patient_id]
    medications_list = []
    for _, med in patient_meds.iterrows():
        desc = str(med.get('Description', ''))
        parts = desc.split(' ', 2)
        med_name = parts[0] if parts else desc
        dosage = parts[1] if len(parts) > 1 else ''
        frequency = parts[2] if len(parts) > 2 else ''
        is_active = str(med.get('Stop', '')) == '' or pd.isna(med.get('Stop', ''))
        if is_active:
            medications_list.append({
                'name': med_name,
                'dosage': dosage,
                'frequency': frequency,
            })

    # Parametri vitali
    vitals = {
        'systolic_bp': int(row.get('systolic_bp', 120)),
        'diastolic_bp': int(row.get('diastolic_bp', 75)),
        'heart_rate': int(row.get('heart_rate', 75)),
        'spo2': round(float(row.get('spo2', 97)), 1),
        'temperature': round(float(row.get('temperature', 36.6)), 1),
        'glucose': int(row.get('glucose', 100)),
        'creatinine': round(float(row.get('creatinine', 1.0)), 2),
        'hemoglobin': round(float(row.get('hemoglobin', 13.0)), 1),
    }

    # Predizione ML
    features_dict = row.to_dict()
    prediction = predictor.predict(features_dict)

    # Data di ricovero
    admission_date = (REFERENCE_DATE - timedelta(days=random.randint(0, 7))).isoformat()

    # Genera note cliniche
    patient_data = {
        'age': int(row['age']),
        'gender': int(row['gender']),
        'department': department,
        'conditions': conditions_list,
        'medications': medications_list,
        'vitals': vitals,
    }
    clinical_notes = generate_clinical_notes(patient_data)

    # Storico encounters (simulato per semplicità)
    encounters_history = []
    admissions_12m = int(row.get('admissions_last_12m', 0))
    for i in range(admissions_12m):
        enc_date = (REFERENCE_DATE - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')
        encounters_history.append({
            'date': enc_date,
            'department': department,
            'los_days': random.randint(3, 12),
            'type': random.choice(['inpatient', 'emergency']),
        })

    # Trend risk score (simulato: 7 giorni)
    base_rs = prediction.risk_score
    risk_trend = []
    for day in range(7, 0, -1):
        date = (REFERENCE_DATE - timedelta(days=day)).strftime('%Y-%m-%d')
        variation = random.randint(-5, 5)
        score = max(1, min(99, base_rs + variation - (7 - day)))
        risk_trend.append({'date': date, 'score': score})
    risk_trend.append({'date': REFERENCE_DATE.strftime('%Y-%m-%d'), 'score': base_rs})

    return {
        'id': patient_id,
        'name': name,
        'age': int(row['age']),
        'gender': gender_char,
        'fiscal_code': fiscal_code,
        'department': department,
        'admission_date': admission_date,
        'is_active': True,
        'conditions': conditions_list[:5],
        'medications': medications_list[:6],
        'vitals': vitals,
        'prediction': {
            'risk_score': prediction.risk_score,
            'risk_level': prediction.risk_level,
            'readmission_probability': prediction.readmission_probability,
            'readmission_label': prediction.readmission_label,
            'predicted_los_days': prediction.predicted_los_days,
            'risk_factors': [
                {
                    'factor': rf.factor,
                    'impact': rf.impact,
                    'contribution': rf.contribution,
                }
                for rf in prediction.risk_factors
            ],
        },
        'risk_trend': risk_trend,
        'encounters_history': encounters_history,
        'clinical_notes': clinical_notes,
    }


def export_json(output_path: str) -> None:
    """Genera il file JSON demo con ~30 pazienti completi."""
    print("=== PatientGuard — Generazione Dati Demo ===\n")

    # Carica dati
    print("1. Caricamento dati...")
    ml_dataset, patients_df, conditions_df, medications_df = load_data()

    # Carica predictor
    print("2. Caricamento modelli ML...")
    predictor = PatientPredictor('backend/ml/models')

    # Seleziona 30 pazienti con distribuzione di rischio variegata
    print("3. Selezione pazienti per il campione demo...")
    sorted_df = ml_dataset.sort_values('risk_score', ascending=False)

    # Prendi pazienti da ogni fascia di rischio
    high_risk = sorted_df[sorted_df['risk_score'] >= 60].head(8)
    medium_risk = sorted_df[(sorted_df['risk_score'] >= 35) & (sorted_df['risk_score'] < 60)].head(12)
    low_risk = sorted_df[sorted_df['risk_score'] < 35].head(10)
    sample_df = pd.concat([high_risk, medium_risk, low_risk])

    # Costruisci record
    print(f"4. Costruzione record per {len(sample_df)} pazienti...")
    patient_records = []
    for _, row in sample_df.iterrows():
        record = build_patient_record(row, patients_df, conditions_df, medications_df, predictor)
        patient_records.append(record)

    # Ordina per risk_score decrescente
    patient_records.sort(key=lambda x: x['prediction']['risk_score'], reverse=True)

    # Salva
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patient_records, f, indent=2, ensure_ascii=False)

    print(f"\n{len(patient_records)} pazienti salvati in {output_path}")

    # Statistiche
    scores = [p['prediction']['risk_score'] for p in patient_records]
    depts = [p['department'] for p in patient_records]
    print(f"\nStatistiche campione demo:")
    print(f"  Risk score: min={min(scores)}, max={max(scores)}, media={np.mean(scores):.1f}")
    print(f"  Reparti: {dict(pd.Series(depts).value_counts())}")
    print(f"  Livelli rischio:")
    for level in ['critico', 'alto', 'medio', 'basso']:
        count = sum(1 for p in patient_records if p['prediction']['risk_level'] == level)
        if count > 0:
            print(f"    {level}: {count}")


def seed_database() -> None:
    """Inserisce i dati demo in Supabase PostgreSQL."""
    print("=== PatientGuard — Seed Database (Supabase) ===\n")

    # Verifica configurazione
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        print("ERRORE: SUPABASE_URL e SUPABASE_KEY devono essere configurati.")
        print("Copia backend/.env.example in .env e compila i valori.")
        print("Oppure usa --mode json per la demo offline.")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("ERRORE: pip install supabase")
        sys.exit(1)

    client = create_client(supabase_url, supabase_key)
    print(f"Connesso a {supabase_url}")

    # Carica il JSON demo come sorgente dati
    json_path = 'data/sample/synthetic_patients.json'
    if not os.path.exists(json_path):
        print(f"ERRORE: {json_path} non trovato. Esegui prima --mode json.")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        patients_data = json.load(f)

    print(f"Caricati {len(patients_data)} pazienti dal JSON demo\n")

    inserted = 0
    for p in patients_data:
        try:
            # 1. Inserisci paziente
            patient_row = {
                'id': p['id'],
                'name': p['name'],
                'age': p['age'],
                'gender': p['gender'],
                'fiscal_code': p.get('fiscal_code', ''),
                'department': p['department'],
                'admission_date': p['admission_date'],
                'is_active': p.get('is_active', True),
            }
            client.table('patients').upsert(patient_row).execute()

            # 2. Condizioni
            for cond in p.get('conditions', []):
                client.table('conditions').insert({
                    'patient_id': p['id'],
                    'icd10_code': cond.get('icd10_code', ''),
                    'description': cond.get('description', ''),
                    'is_active': cond.get('is_active', True),
                }).execute()

            # 3. Farmaci
            for med in p.get('medications', []):
                client.table('medications').insert({
                    'patient_id': p['id'],
                    'name': med.get('name', ''),
                    'dosage': med.get('dosage', ''),
                    'frequency': med.get('frequency', ''),
                    'is_active': True,
                }).execute()

            # 4. Vitali
            vitals = p.get('vitals', {})
            if vitals:
                client.table('vitals').insert({
                    'patient_id': p['id'],
                    'systolic_bp': vitals.get('systolic_bp'),
                    'diastolic_bp': vitals.get('diastolic_bp'),
                    'heart_rate': vitals.get('heart_rate'),
                    'spo2': vitals.get('spo2'),
                    'temperature': vitals.get('temperature'),
                    'glucose': vitals.get('glucose'),
                    'creatinine': vitals.get('creatinine'),
                    'hemoglobin': vitals.get('hemoglobin'),
                }).execute()

            # 5. Predizione
            pred = p.get('prediction', {})
            if pred:
                client.table('predictions').insert({
                    'patient_id': p['id'],
                    'risk_score': pred.get('risk_score', 0),
                    'readmission_prob': pred.get('readmission_probability', 0),
                    'predicted_los': pred.get('predicted_los_days', 0),
                    'risk_factors': json.dumps(pred.get('risk_factors', [])),
                    'model_version': '1.0.0',
                }).execute()

            # 6. Note cliniche
            for note in p.get('clinical_notes', []):
                client.table('clinical_notes').insert({
                    'patient_id': p['id'],
                    'author': note.get('author', ''),
                    'note_type': note.get('note_type', ''),
                    'content': note.get('content', ''),
                    'timestamp': note.get('timestamp'),
                }).execute()

            # 7. Encounter storici
            for enc in p.get('encounters_history', []):
                client.table('encounters').insert({
                    'patient_id': p['id'],
                    'encounter_type': enc.get('type', 'inpatient'),
                    'department': enc.get('department', ''),
                    'admission_date': enc.get('date'),
                    'los_days': enc.get('los_days', 0),
                }).execute()

            # 8. Alert per pazienti ad alto rischio
            risk_level = pred.get('risk_level', 'basso')
            if risk_level in ('critico', 'alto'):
                severity = 'critical' if risk_level == 'critico' else 'high'
                client.table('alerts').insert({
                    'patient_id': p['id'],
                    'alert_type': 'risk_increase',
                    'severity': severity,
                    'message': f"{p['name']}: risk score {pred.get('risk_score', 0)}/100 — livello {risk_level.upper()}.",
                }).execute()

            inserted += 1
            print(f"  [{inserted}/{len(patients_data)}] {p['name']} — {p['department']}")

        except Exception as e:
            print(f"  ERRORE per {p.get('name', '?')}: {e}")

    print(f"\nSeed completato: {inserted}/{len(patients_data)} pazienti inseriti in Supabase.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed dati PatientGuard')
    parser.add_argument('--mode', type=str, choices=['json', 'db'], default='json',
                        help="'json' genera il file demo, 'db' inserisce in Supabase")
    parser.add_argument('--output', type=str, default='data/sample/synthetic_patients.json',
                        help='Path del file JSON di output')
    args = parser.parse_args()

    if args.mode == 'json':
        export_json(args.output)
    else:
        seed_database()
