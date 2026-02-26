"""
Generatore di dati sintetici in formato Synthea CSV per PatientGuard.

Produce 1000 pazienti sintetici con dati localizzati per il SSN italiano.
I CSV generati hanno lo stesso schema dei file Synthea reali, permettendo
alla pipeline di preprocessing di funzionare con entrambe le fonti.

Uso:
    python3 data/generate_synthea.py --num-patients 1000 --output-dir data/synthea_output

Output:
    patients.csv, conditions.csv, medications.csv, observations.csv,
    encounters.csv, procedures.csv, allergies.csv
"""

import argparse
import os
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from faker import Faker

# Seed per riproducibilità
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

fake = Faker('it_IT')
Faker.seed(SEED)

# =============================================================================
# COSTANTI E CONFIGURAZIONE
# =============================================================================

# Data di riferimento per la generazione
REFERENCE_DATE = datetime(2026, 2, 20)

# Reparti ospedalieri SSN
DEPARTMENTS = [
    'Medicina Interna',
    'Cardiologia',
    'Pneumologia',
    'Nefrologia',
    'Geriatria',
]

# Regioni e città italiane
ITALIAN_LOCATIONS = [
    ('Milano', 'Lombardia', '20100', 45.4642, 9.1900),
    ('Roma', 'Lazio', '00100', 41.9028, 12.4964),
    ('Napoli', 'Campania', '80100', 40.8518, 14.2681),
    ('Torino', 'Piemonte', '10100', 45.0703, 7.6869),
    ('Bologna', 'Emilia-Romagna', '40100', 44.4949, 11.3426),
    ('Firenze', 'Toscana', '50100', 43.7696, 11.2558),
    ('Palermo', 'Sicilia', '90100', 38.1157, 13.3615),
    ('Genova', 'Liguria', '16100', 44.4056, 8.9463),
    ('Bari', 'Puglia', '70100', 41.1171, 16.8719),
    ('Bergamo', 'Lombardia', '24100', 45.6983, 9.6773),
]

# Profili clinici — ogni paziente viene assegnato a uno di questi
CLINICAL_PROFILES = {
    'cardiopatico': {
        'weight': 0.25,
        'age_range': (55, 90),
        'conditions': [
            ('84114007', 'Heart failure', 'I50.9', 0.9),
            ('38341003', 'Hypertension', 'I10', 0.85),
            ('49436004', 'Atrial fibrillation', 'I48.91', 0.4),
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.35),
            ('53741008', 'Coronary artery disease', 'I25.10', 0.5),
        ],
        'medications': [
            ('Furosemide', '40mg', '1x/die', 0.85),
            ('Ramipril', '5mg', '1x/die', 0.7),
            ('Bisoprololo', '2.5mg', '1x/die', 0.65),
            ('Warfarin', '5mg', '1x/die', 0.35),
            ('Atorvastatina', '20mg', '1x/die', 0.5),
            ('Spironolattone', '25mg', '1x/die', 0.3),
        ],
        'vitals_profile': {
            'systolic_bp': (130, 175, 15),
            'diastolic_bp': (75, 100, 10),
            'heart_rate': (70, 110, 15),
            'spo2': (91, 98, 2),
            'temperature': (36.2, 37.2, 0.3),
            'glucose': (90, 180, 30),
            'creatinine': (1.0, 2.5, 0.4),
            'hemoglobin': (10.0, 14.0, 1.5),
        },
        'readmission_prob': 0.30,
        'avg_los': (5, 12),
        'deterioration_prob': 0.10,
    },
    'bpco': {
        'weight': 0.20,
        'age_range': (50, 85),
        'conditions': [
            ('13645005', 'COPD', 'J44.1', 0.95),
            ('38341003', 'Hypertension', 'I10', 0.5),
            ('195967001', 'Asthma', 'J45.909', 0.25),
            ('84114007', 'Heart failure', 'I50.9', 0.20),
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.25),
        ],
        'medications': [
            ('Salbutamolo', '100mcg', '4x/die', 0.9),
            ('Tiotropio', '18mcg', '1x/die', 0.75),
            ('Prednisone', '25mg', '1x/die', 0.4),
            ('Fluticasone', '250mcg', '2x/die', 0.5),
            ('Amoxicillina', '1g', '3x/die', 0.3),
        ],
        'vitals_profile': {
            'systolic_bp': (110, 150, 15),
            'diastolic_bp': (65, 90, 10),
            'heart_rate': (75, 105, 12),
            'spo2': (85, 95, 3),
            'temperature': (36.0, 38.5, 0.6),
            'glucose': (80, 150, 25),
            'creatinine': (0.8, 1.6, 0.3),
            'hemoglobin': (11.0, 15.0, 1.2),
        },
        'readmission_prob': 0.25,
        'avg_los': (4, 10),
        'deterioration_prob': 0.08,
    },
    'diabetico': {
        'weight': 0.20,
        'age_range': (45, 80),
        'conditions': [
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.95),
            ('38341003', 'Hypertension', 'I10', 0.65),
            ('431855005', 'Chronic kidney disease', 'N18.3', 0.30),
            ('53741008', 'Coronary artery disease', 'I25.10', 0.25),
            ('368581000119106', 'Diabetic neuropathy', 'E11.40', 0.20),
        ],
        'medications': [
            ('Metformina', '850mg', '2x/die', 0.85),
            ('Insulina Glargine', '20UI', '1x/die', 0.4),
            ('Ramipril', '5mg', '1x/die', 0.55),
            ('Atorvastatina', '20mg', '1x/die', 0.5),
            ('Amlodipina', '5mg', '1x/die', 0.35),
        ],
        'vitals_profile': {
            'systolic_bp': (120, 160, 15),
            'diastolic_bp': (70, 95, 10),
            'heart_rate': (65, 95, 10),
            'spo2': (94, 99, 1.5),
            'temperature': (36.2, 37.0, 0.3),
            'glucose': (100, 300, 60),
            'creatinine': (0.9, 2.0, 0.4),
            'hemoglobin': (10.5, 14.5, 1.3),
        },
        'readmission_prob': 0.20,
        'avg_los': (3, 8),
        'deterioration_prob': 0.05,
    },
    'nefropatico': {
        'weight': 0.15,
        'age_range': (50, 85),
        'conditions': [
            ('431855005', 'Chronic kidney disease', 'N18.3', 0.95),
            ('38341003', 'Hypertension', 'I10', 0.80),
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.45),
            ('84114007', 'Heart failure', 'I50.9', 0.30),
            ('271737000', 'Anemia', 'D64.9', 0.50),
        ],
        'medications': [
            ('Furosemide', '80mg', '1x/die', 0.7),
            ('Amlodipina', '10mg', '1x/die', 0.6),
            ('Eritropoietina', '4000UI', '3x/settimana', 0.4),
            ('Calcio carbonato', '1g', '3x/die', 0.5),
            ('Ramipril', '2.5mg', '1x/die', 0.5),
            ('Sodio bicarbonato', '500mg', '3x/die', 0.3),
        ],
        'vitals_profile': {
            'systolic_bp': (130, 180, 18),
            'diastolic_bp': (75, 105, 12),
            'heart_rate': (65, 100, 12),
            'spo2': (93, 98, 2),
            'temperature': (36.0, 37.2, 0.3),
            'glucose': (80, 200, 40),
            'creatinine': (2.0, 5.0, 0.8),
            'hemoglobin': (8.0, 12.0, 1.5),
        },
        'readmission_prob': 0.35,
        'avg_los': (5, 14),
        'deterioration_prob': 0.12,
    },
    'geriatrico': {
        'weight': 0.15,
        'age_range': (75, 95),
        'conditions': [
            ('38341003', 'Hypertension', 'I10', 0.85),
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.40),
            ('84114007', 'Heart failure', 'I50.9', 0.35),
            ('69896004', 'Rheumatoid arthritis', 'M06.9', 0.25),
            ('386806002', 'Impaired cognition', 'R41.89', 0.30),
            ('271737000', 'Anemia', 'D64.9', 0.35),
        ],
        'medications': [
            ('Amlodipina', '5mg', '1x/die', 0.6),
            ('Omeprazolo', '20mg', '1x/die', 0.55),
            ('Paracetamolo', '1g', '3x/die', 0.45),
            ('Furosemide', '25mg', '1x/die', 0.4),
            ('Atorvastatina', '10mg', '1x/die', 0.35),
            ('Enoxaparina', '4000UI', '1x/die', 0.30),
        ],
        'vitals_profile': {
            'systolic_bp': (110, 170, 20),
            'diastolic_bp': (60, 95, 12),
            'heart_rate': (55, 95, 15),
            'spo2': (90, 97, 2.5),
            'temperature': (35.8, 37.5, 0.4),
            'glucose': (70, 180, 35),
            'creatinine': (0.9, 2.5, 0.5),
            'hemoglobin': (9.0, 13.0, 1.5),
        },
        'readmission_prob': 0.30,
        'avg_los': (6, 15),
        'deterioration_prob': 0.15,
    },
    'post_chirurgico': {
        'weight': 0.05,
        'age_range': (30, 65),
        'conditions': [
            ('38341003', 'Hypertension', 'I10', 0.30),
            ('44054006', 'Diabetes mellitus type 2', 'E11.9', 0.15),
            ('40055000', 'Chronic pain', 'G89.29', 0.40),
        ],
        'medications': [
            ('Paracetamolo', '1g', '3x/die', 0.8),
            ('Ketorolac', '30mg', '2x/die', 0.5),
            ('Enoxaparina', '4000UI', '1x/die', 0.7),
            ('Amoxicillina', '1g', '3x/die', 0.4),
        ],
        'vitals_profile': {
            'systolic_bp': (110, 140, 10),
            'diastolic_bp': (65, 85, 8),
            'heart_rate': (60, 90, 10),
            'spo2': (95, 99, 1.5),
            'temperature': (36.2, 37.8, 0.5),
            'glucose': (75, 140, 20),
            'creatinine': (0.7, 1.3, 0.2),
            'hemoglobin': (10.5, 15.0, 1.2),
        },
        'readmission_prob': 0.10,
        'avg_los': (2, 6),
        'deterioration_prob': 0.03,
    },
}

# Procedure comuni per profilo
PROCEDURES = {
    'cardiopatico': [
        ('B272', 'Ecocardiogramma', 'SNOMED', 0.6),
        ('B245', 'Elettrocardiogramma', 'SNOMED', 0.8),
        ('B241', 'Holter ECG 24h', 'SNOMED', 0.3),
    ],
    'bpco': [
        ('B311', 'Spirometria', 'SNOMED', 0.7),
        ('B314', 'Emogasanalisi', 'SNOMED', 0.6),
        ('B320', 'Radiografia torace', 'SNOMED', 0.5),
    ],
    'diabetico': [
        ('B905', 'Fondo oculare', 'SNOMED', 0.4),
        ('B272', 'Ecocardiogramma', 'SNOMED', 0.3),
        ('B441', 'Ecografia renale', 'SNOMED', 0.25),
    ],
    'nefropatico': [
        ('B441', 'Ecografia renale', 'SNOMED', 0.6),
        ('B272', 'Ecocardiogramma', 'SNOMED', 0.4),
        ('B314', 'Emogasanalisi', 'SNOMED', 0.3),
    ],
    'geriatrico': [
        ('B245', 'Elettrocardiogramma', 'SNOMED', 0.5),
        ('B320', 'Radiografia torace', 'SNOMED', 0.4),
        ('B272', 'Ecocardiogramma', 'SNOMED', 0.3),
    ],
    'post_chirurgico': [
        ('B320', 'Radiografia torace', 'SNOMED', 0.4),
        ('B245', 'Elettrocardiogramma', 'SNOMED', 0.3),
    ],
}

# Allergie comuni
ALLERGIES = [
    ('7980', 'SNOMED', 'Penicillin allergy', 'allergy', 'medication', 0.08),
    ('300916003', 'SNOMED', 'Latex allergy', 'allergy', 'environment', 0.03),
    ('419474003', 'SNOMED', 'Allergy to sulfonamide', 'allergy', 'medication', 0.04),
    ('418689008', 'SNOMED', 'Allergy to aspirin', 'allergy', 'medication', 0.05),
    ('91936005', 'SNOMED', 'Allergy to peanuts', 'allergy', 'food', 0.02),
]

# Codici LOINC per osservazioni
LOINC_CODES = {
    'systolic_bp': ('8480-6', 'Systolic Blood Pressure', 'mmHg'),
    'diastolic_bp': ('8462-4', 'Diastolic Blood Pressure', 'mmHg'),
    'heart_rate': ('8867-4', 'Heart rate', 'beats/min'),
    'spo2': ('59408-5', 'Oxygen saturation', '%'),
    'temperature': ('8310-5', 'Body temperature', 'Cel'),
    'glucose': ('2339-0', 'Glucose [Mass/volume] in Blood', 'mg/dL'),
    'creatinine': ('38483-4', 'Creatinine [Mass/volume] in Blood', 'mg/dL'),
    'hemoglobin': ('718-7', 'Hemoglobin [Mass/volume] in Blood', 'g/dL'),
}


# =============================================================================
# GENERATORE DI CODICE FISCALE SINTETICO
# =============================================================================

def genera_codice_fiscale(nome: str, cognome: str, data_nascita: datetime,
                          sesso: str) -> str:
    """Genera un codice fiscale italiano sintetico (non validato)."""
    # Consonanti del cognome
    consonanti = [c for c in cognome.upper() if c.isalpha() and c not in 'AEIOU']
    vocali = [c for c in cognome.upper() if c in 'AEIOU']
    cf_cognome = ''.join((consonanti + vocali + ['X', 'X', 'X'])[:3])

    # Consonanti del nome
    consonanti = [c for c in nome.upper() if c.isalpha() and c not in 'AEIOU']
    vocali = [c for c in nome.upper() if c in 'AEIOU']
    if len(consonanti) >= 4:
        cf_nome = consonanti[0] + consonanti[2] + consonanti[3]
    else:
        cf_nome = ''.join((consonanti + vocali + ['X', 'X', 'X'])[:3])

    # Anno e mese
    anno = str(data_nascita.year)[-2:]
    mesi = 'ABCDEHLMPRST'
    mese = mesi[data_nascita.month - 1]

    # Giorno (+ 40 per le donne)
    giorno = data_nascita.day
    if sesso == 'F':
        giorno += 40
    giorno_str = f'{giorno:02d}'

    # Codice comune (sintetico)
    codice_comune = random.choice(['F205', 'H501', 'F839', 'L219', 'A944',
                                    'D612', 'G273', 'D969', 'A662', 'A794'])

    # Carattere di controllo (semplificato: lettera random)
    controllo = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    return f'{cf_cognome}{cf_nome}{anno}{mese}{giorno_str}{codice_comune}{controllo}'


# =============================================================================
# FUNZIONI DI GENERAZIONE
# =============================================================================

def select_clinical_profile() -> str:
    """Seleziona un profilo clinico in base ai pesi definiti."""
    profiles = list(CLINICAL_PROFILES.keys())
    weights = [CLINICAL_PROFILES[p]['weight'] for p in profiles]
    return random.choices(profiles, weights=weights, k=1)[0]


def generate_patient(patient_idx: int) -> dict:
    """Genera un singolo paziente con tutti i suoi dati."""
    patient_id = str(uuid.uuid4())
    profile_name = select_clinical_profile()
    profile = CLINICAL_PROFILES[profile_name]

    # Dati demografici
    sesso = random.choice(['M', 'F'])
    age = random.randint(*profile['age_range'])
    birth_date = REFERENCE_DATE - timedelta(days=age * 365 + random.randint(0, 364))

    if sesso == 'M':
        first_name = fake.first_name_male()
    else:
        first_name = fake.first_name_female()
    last_name = fake.last_name()

    location = random.choice(ITALIAN_LOCATIONS)
    city, state, zip_code, lat, lon = location

    cf = genera_codice_fiscale(first_name, last_name, birth_date, sesso)

    # Possibile decesso (bassa probabilità per i più anziani/gravi)
    death_date = None
    if age > 80 and random.random() < 0.03:
        death_date = REFERENCE_DATE - timedelta(days=random.randint(0, 30))

    patient_data = {
        'Id': patient_id,
        'BirthDate': birth_date.strftime('%Y-%m-%d'),
        'DeathDate': death_date.strftime('%Y-%m-%d') if death_date else '',
        'SSN': cf,  # Codice Fiscale al posto del SSN americano
        'Prefix': random.choice(['Sig.', 'Sig.ra', 'Dott.', 'Dott.ssa']) if random.random() < 0.3 else '',
        'First': first_name,
        'Middle': '',
        'Last': last_name,
        'Suffix': '',
        'Maiden': fake.last_name() if sesso == 'F' and random.random() < 0.3 else '',
        'Marital': random.choice(['M', 'S', 'D', 'W']),
        'Race': 'white',
        'Ethnicity': 'italian',
        'Gender': sesso,
        'BirthPlace': f'{city}, {state}',
        'Address': fake.street_address(),
        'City': city,
        'State': state,
        'County': state,
        'Zip': zip_code,
        'Lat': lat + random.uniform(-0.05, 0.05),
        'Lon': lon + random.uniform(-0.05, 0.05),
        'Healthcare_Expenses': round(random.uniform(5000, 50000), 2),
        'Healthcare_Coverage': round(random.uniform(3000, 40000), 2),
        'Income': round(random.uniform(15000, 60000), 2),
        # Metadati extra (non Synthea, utili per noi)
        '_profile': profile_name,
        '_age': age,
    }

    return patient_data


def generate_encounters_for_patient(patient_id: str, profile_name: str,
                                     age: int) -> list[dict]:
    """Genera ricoveri e visite per un paziente."""
    profile = CLINICAL_PROFILES[profile_name]
    encounters = []

    # Assegna un reparto primario basato sul profilo
    dept_weights = {
        'cardiopatico': [0.1, 0.7, 0.05, 0.05, 0.1],
        'bpco': [0.15, 0.05, 0.65, 0.05, 0.1],
        'diabetico': [0.5, 0.1, 0.05, 0.15, 0.2],
        'nefropatico': [0.1, 0.05, 0.05, 0.7, 0.1],
        'geriatrico': [0.3, 0.15, 0.1, 0.1, 0.35],
        'post_chirurgico': [0.6, 0.1, 0.05, 0.05, 0.2],
    }
    primary_dept = random.choices(DEPARTMENTS, weights=dept_weights[profile_name], k=1)[0]

    # Ricovero attuale (inpatient)
    admission_date = REFERENCE_DATE - timedelta(days=random.randint(0, 7))
    los = random.randint(*profile['avg_los'])
    discharge_date = admission_date + timedelta(days=los)

    # Se non ancora dimesso
    if discharge_date > REFERENCE_DATE:
        discharge_date = None

    current_encounter = {
        'Id': str(uuid.uuid4()),
        'Start': admission_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'Stop': discharge_date.strftime('%Y-%m-%dT%H:%M:%SZ') if discharge_date else '',
        'Patient': patient_id,
        'Organization': f'Ospedale di {random.choice(["Milano", "Roma", "Torino", "Bologna", "Napoli"])}',
        'Provider': str(uuid.uuid4()),
        'Payer': 'SSN',
        'EncounterClass': 'inpatient',
        'Code': '183452005',
        'Description': f'Ricovero {primary_dept}',
        'Base_Encounter_Cost': round(random.uniform(500, 2000), 2),
        'Total_Claim_Cost': round(random.uniform(1000, 5000), 2),
        'Payer_Coverage': round(random.uniform(800, 4000), 2),
        'ReasonCode': '',
        'ReasonDescription': '',
        '_department': primary_dept,
        '_is_current': True,
    }
    encounters.append(current_encounter)

    # Ricoveri precedenti (0-4 negli ultimi 12 mesi)
    n_previous = np.random.poisson(lam=1.5)
    n_previous = min(n_previous, 4)

    for i in range(n_previous):
        prev_admission = admission_date - timedelta(days=random.randint(30, 365))
        prev_los = random.randint(2, max(3, los + random.randint(-3, 3)))
        prev_discharge = prev_admission + timedelta(days=prev_los)

        dept = random.choices(DEPARTMENTS, weights=dept_weights[profile_name], k=1)[0]

        prev_encounter = {
            'Id': str(uuid.uuid4()),
            'Start': prev_admission.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Stop': prev_discharge.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Patient': patient_id,
            'Organization': current_encounter['Organization'],
            'Provider': str(uuid.uuid4()),
            'Payer': 'SSN',
            'EncounterClass': random.choices(
                ['inpatient', 'outpatient', 'emergency'],
                weights=[0.5, 0.3, 0.2], k=1
            )[0],
            'Code': '183452005',
            'Description': f'Ricovero {dept}',
            'Base_Encounter_Cost': round(random.uniform(300, 1500), 2),
            'Total_Claim_Cost': round(random.uniform(500, 3000), 2),
            'Payer_Coverage': round(random.uniform(400, 2500), 2),
            'ReasonCode': '',
            'ReasonDescription': '',
            '_department': dept,
            '_is_current': False,
        }
        encounters.append(prev_encounter)

    # Visite ambulatoriali (1-3)
    n_outpatient = random.randint(1, 3)
    for _ in range(n_outpatient):
        visit_date = admission_date - timedelta(days=random.randint(14, 180))
        encounters.append({
            'Id': str(uuid.uuid4()),
            'Start': visit_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Stop': visit_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Patient': patient_id,
            'Organization': current_encounter['Organization'],
            'Provider': str(uuid.uuid4()),
            'Payer': 'SSN',
            'EncounterClass': 'outpatient',
            'Code': '185349003',
            'Description': f'Visita ambulatoriale {primary_dept}',
            'Base_Encounter_Cost': round(random.uniform(50, 200), 2),
            'Total_Claim_Cost': round(random.uniform(100, 400), 2),
            'Payer_Coverage': round(random.uniform(80, 350), 2),
            'ReasonCode': '',
            'ReasonDescription': '',
            '_department': primary_dept,
            '_is_current': False,
        })

    return encounters


def generate_conditions_for_patient(patient_id: str, profile_name: str,
                                     encounters: list[dict]) -> list[dict]:
    """Genera condizioni/diagnosi per un paziente."""
    profile = CLINICAL_PROFILES[profile_name]
    conditions = []

    # Seleziona condizioni in base alla probabilità del profilo
    for snomed_code, description, icd10, prob in profile['conditions']:
        if random.random() < prob:
            # Data di inizio: da qualche anno fa
            onset = REFERENCE_DATE - timedelta(days=random.randint(180, 3650))
            # Alcune condizioni si risolvono
            stop = ''
            if random.random() < 0.1:
                stop = (onset + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')

            # Associa all'encounter corrente o a uno precedente
            enc_id = encounters[0]['Id'] if encounters else ''
            if len(encounters) > 1 and random.random() < 0.3:
                enc_id = random.choice(encounters)['Id']

            conditions.append({
                'Start': onset.strftime('%Y-%m-%d'),
                'Stop': stop,
                'Patient': patient_id,
                'Encounter': enc_id,
                'System': 'SNOMED-CT',
                'Code': snomed_code,
                'Description': description,
            })

    return conditions


def generate_medications_for_patient(patient_id: str, profile_name: str,
                                      encounters: list[dict]) -> list[dict]:
    """Genera prescrizioni farmacologiche per un paziente."""
    profile = CLINICAL_PROFILES[profile_name]
    medications = []

    for med_name, dosage, frequency, prob in profile['medications']:
        if random.random() < prob:
            start = REFERENCE_DATE - timedelta(days=random.randint(30, 730))
            # Alcuni farmaci hanno una data di fine
            stop = ''
            if random.random() < 0.15:
                stop = (start + timedelta(days=random.randint(14, 180))).strftime('%Y-%m-%dT%H:%M:%SZ')

            enc_id = encounters[0]['Id'] if encounters else ''

            medications.append({
                'Start': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'Stop': stop,
                'Patient': patient_id,
                'Payer': 'SSN',
                'Encounter': enc_id,
                'Code': str(random.randint(100000, 999999)),  # Codice RxNorm sintetico
                'Description': f'{med_name} {dosage} {frequency}',
                'Base_Cost': round(random.uniform(2, 50), 2),
                'Payer_Coverage': round(random.uniform(1, 40), 2),
                'Dispenses': random.randint(1, 12),
                'TotalCost': round(random.uniform(10, 200), 2),
                'ReasonCode': '',
                'ReasonDescription': '',
            })

    return medications


def generate_observations_for_patient(patient_id: str, profile_name: str,
                                       encounters: list[dict]) -> list[dict]:
    """Genera parametri vitali e valori di laboratorio per un paziente."""
    profile = CLINICAL_PROFILES[profile_name]
    vitals = profile['vitals_profile']
    observations = []

    for encounter in encounters:
        enc_id = encounter['Id']
        enc_start = datetime.strptime(encounter['Start'], '%Y-%m-%dT%H:%M:%SZ')

        # Determina quante osservazioni generare
        if encounter['EncounterClass'] == 'inpatient':
            n_obs_sets = random.randint(3, 8)
        else:
            n_obs_sets = random.randint(1, 2)

        for obs_idx in range(n_obs_sets):
            # Timestamp dell'osservazione
            obs_time = enc_start + timedelta(hours=obs_idx * random.randint(4, 12))

            # Genera ogni parametro vitale
            for vital_key, (loinc_code, description, unit) in LOINC_CODES.items():
                if vital_key in vitals:
                    low, high, noise = vitals[vital_key]
                    base_value = random.uniform(low, high)
                    # Aggiunge rumore gaussiano
                    value = base_value + np.random.normal(0, noise)

                    # Arrotondamento appropriato
                    if vital_key in ('systolic_bp', 'diastolic_bp', 'heart_rate', 'glucose'):
                        value = int(round(value))
                    elif vital_key == 'spo2':
                        value = round(min(100, max(70, value)), 1)
                    else:
                        value = round(value, 2)

                    observations.append({
                        'Date': obs_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'Patient': patient_id,
                        'Encounter': enc_id,
                        'Category': 'vital-signs' if vital_key in ('systolic_bp', 'diastolic_bp', 'heart_rate', 'spo2', 'temperature') else 'laboratory',
                        'Code': loinc_code,
                        'Description': description,
                        'Value': str(value),
                        'Units': unit,
                        'Type': 'numeric',
                    })

    return observations


def generate_procedures_for_patient(patient_id: str, profile_name: str,
                                     encounters: list[dict]) -> list[dict]:
    """Genera procedure per un paziente."""
    procedures = []
    profile_procs = PROCEDURES.get(profile_name, [])

    for encounter in encounters:
        if encounter['EncounterClass'] != 'inpatient':
            continue

        enc_start = datetime.strptime(encounter['Start'], '%Y-%m-%dT%H:%M:%SZ')

        for code, description, system, prob in profile_procs:
            if random.random() < prob:
                proc_time = enc_start + timedelta(hours=random.randint(2, 48))
                procedures.append({
                    'Start': proc_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'Stop': (proc_time + timedelta(minutes=random.randint(15, 120))).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'Patient': patient_id,
                    'Encounter': encounter['Id'],
                    'System': system,
                    'Code': code,
                    'Description': description,
                    'Base_Cost': round(random.uniform(50, 500), 2),
                    'ReasonCode': '',
                    'ReasonDescription': '',
                })

    return procedures


def generate_allergies_for_patient(patient_id: str,
                                    encounters: list[dict]) -> list[dict]:
    """Genera allergie per un paziente."""
    allergies = []

    for code, system, description, allergy_type, category, prob in ALLERGIES:
        if random.random() < prob:
            start = REFERENCE_DATE - timedelta(days=random.randint(365, 7300))
            enc_id = encounters[0]['Id'] if encounters else ''

            allergies.append({
                'Start': start.strftime('%Y-%m-%d'),
                'Stop': '',
                'Patient': patient_id,
                'Encounter': enc_id,
                'Code': code,
                'System': system,
                'Description': description,
                'Type': allergy_type,
                'Category': category,
            })

    return allergies


# =============================================================================
# FUNZIONE PRINCIPALE
# =============================================================================

def generate_dataset(num_patients: int, output_dir: str) -> None:
    """Genera l'intero dataset sintetico."""
    print(f"Generazione di {num_patients} pazienti sintetici...")

    all_patients = []
    all_encounters = []
    all_conditions = []
    all_medications = []
    all_observations = []
    all_procedures = []
    all_allergies = []

    for i in range(num_patients):
        if (i + 1) % 100 == 0:
            print(f"  Generati {i + 1}/{num_patients} pazienti...")

        # 1. Genera paziente
        patient = generate_patient(i)
        patient_id = patient['Id']
        profile_name = patient['_profile']
        age = patient['_age']

        # 2. Genera encounters
        encounters = generate_encounters_for_patient(patient_id, profile_name, age)

        # 3. Genera condizioni
        conditions = generate_conditions_for_patient(patient_id, profile_name, encounters)

        # 4. Genera farmaci
        medications = generate_medications_for_patient(patient_id, profile_name, encounters)

        # 5. Genera osservazioni (vitali + lab)
        observations = generate_observations_for_patient(patient_id, profile_name, encounters)

        # 6. Genera procedure
        procedures = generate_procedures_for_patient(patient_id, profile_name, encounters)

        # 7. Genera allergie
        allergies = generate_allergies_for_patient(patient_id, encounters)

        # Accumula
        all_patients.append(patient)
        all_encounters.extend(encounters)
        all_conditions.extend(conditions)
        all_medications.extend(medications)
        all_observations.extend(observations)
        all_procedures.extend(procedures)
        all_allergies.extend(allergies)

    # Salva CSV
    os.makedirs(output_dir, exist_ok=True)

    # Rimuovi colonne interne (_profile, _age, _department, _is_current)
    patients_df = pd.DataFrame(all_patients)
    patients_df = patients_df.drop(columns=[c for c in patients_df.columns if c.startswith('_')])
    patients_df.to_csv(os.path.join(output_dir, 'patients.csv'), index=False)

    encounters_df = pd.DataFrame(all_encounters)
    encounters_df_clean = encounters_df.drop(columns=[c for c in encounters_df.columns if c.startswith('_')])
    encounters_df_clean.to_csv(os.path.join(output_dir, 'encounters.csv'), index=False)

    # Salva anche la versione con metadati per preprocessing interno
    encounters_df.to_csv(os.path.join(output_dir, 'encounters_meta.csv'), index=False)

    pd.DataFrame(all_conditions).to_csv(os.path.join(output_dir, 'conditions.csv'), index=False)
    pd.DataFrame(all_medications).to_csv(os.path.join(output_dir, 'medications.csv'), index=False)
    pd.DataFrame(all_observations).to_csv(os.path.join(output_dir, 'observations.csv'), index=False)
    pd.DataFrame(all_procedures).to_csv(os.path.join(output_dir, 'procedures.csv'), index=False)
    pd.DataFrame(all_allergies).to_csv(os.path.join(output_dir, 'allergies.csv'), index=False)

    # Statistiche
    print(f"\nDataset generato in {output_dir}/")
    print(f"  Pazienti:      {len(all_patients)}")
    print(f"  Encounters:    {len(all_encounters)}")
    print(f"  Condizioni:    {len(all_conditions)}")
    print(f"  Farmaci:       {len(all_medications)}")
    print(f"  Osservazioni:  {len(all_observations)}")
    print(f"  Procedure:     {len(all_procedures)}")
    print(f"  Allergie:      {len(all_allergies)}")

    # Distribuzione profili clinici
    profiles = pd.DataFrame(all_patients)['_profile'].value_counts()
    print(f"\nDistribuzione profili clinici:")
    for profile, count in profiles.items():
        print(f"  {profile}: {count} ({count/len(all_patients)*100:.1f}%)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Genera dati sintetici PatientGuard')
    parser.add_argument('--num-patients', type=int, default=1000,
                        help='Numero di pazienti da generare (default: 1000)')
    parser.add_argument('--output-dir', type=str, default='data/synthea_output',
                        help='Directory di output per i CSV')
    args = parser.parse_args()

    generate_dataset(args.num_patients, args.output_dir)
