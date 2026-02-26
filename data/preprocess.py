"""
Preprocessamento dati Synthea -> dataset ML tabellare.

Ogni riga = un encounter di tipo 'inpatient' con feature aggregate del paziente.
Carica i CSV generati da generate_synthea.py, estrae le feature e calcola i target.

Uso:
    cd patientguard
    python3 data/preprocess.py --input-dir data/synthea_output --output-dir data/processed

Output:
    data/processed/ml_dataset.csv
"""

import argparse
import os
import sys
import warnings

import numpy as np
import pandas as pd

# Aggiungi la root del progetto al path per import backend.ml.*
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.ml.features import (
    ML_FEATURE_COLUMNS,
    TARGET_COLUMNS,
    extract_clinical_features,
    extract_demographics,
    extract_historical_features,
    extract_lab_features,
    extract_temporal_features,
    extract_vital_signs,
)
from backend.ml.pipeline import (
    compute_base_risk_score,
    compute_deterioration,
    compute_los_days,
    compute_readmission_30d,
)

warnings.filterwarnings('ignore', category=FutureWarning)


# =============================================================================
# CARICAMENTO DATI
# =============================================================================

def load_synthea_csvs(input_dir: str) -> dict[str, pd.DataFrame]:
    """
    Carica tutti i CSV Synthea con parsing date appropriato.

    Returns:
        Dizionario {nome_file: DataFrame}
    """
    required_files = [
        'patients.csv', 'encounters.csv', 'conditions.csv',
        'medications.csv', 'observations.csv', 'procedures.csv',
    ]

    dataframes = {}
    for filename in required_files:
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File non trovato: {filepath}")

        df = pd.read_csv(filepath, low_memory=False)
        key = filename.replace('.csv', '')
        dataframes[key] = df
        print(f"  Caricato {filename}: {len(df)} righe")

    # Carica encounters con metadati se disponibile
    meta_path = os.path.join(input_dir, 'encounters_meta.csv')
    if os.path.exists(meta_path):
        dataframes['encounters_meta'] = pd.read_csv(meta_path, low_memory=False)
        print(f"  Caricato encounters_meta.csv: {len(dataframes['encounters_meta'])} righe")
    else:
        dataframes['encounters_meta'] = dataframes['encounters']

    return dataframes


def filter_inpatient_encounters(encounters_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra solo i ricoveri (EncounterClass == 'inpatient').
    Prende solo l'encounter corrente (il più recente per paziente).
    """
    inpatient = encounters_df[encounters_df['EncounterClass'] == 'inpatient'].copy()

    if '_is_current' in inpatient.columns:
        # Usa il flag del generatore
        current = inpatient[inpatient['_is_current'] == True]
        if len(current) > 0:
            return current

    # Fallback: prendi l'encounter più recente per paziente
    inpatient['Start'] = pd.to_datetime(inpatient['Start'], errors='coerce')
    inpatient = inpatient.sort_values('Start', ascending=False)
    current = inpatient.groupby('Patient').first().reset_index()

    return current


# =============================================================================
# COSTRUZIONE MATRICE FEATURE
# =============================================================================

def build_feature_matrix(patients_df: pd.DataFrame,
                          encounters_df: pd.DataFrame,
                          encounters_meta_df: pd.DataFrame,
                          conditions_df: pd.DataFrame,
                          medications_df: pd.DataFrame,
                          observations_df: pd.DataFrame,
                          procedures_df: pd.DataFrame) -> pd.DataFrame:
    """
    Per ogni encounter inpatient corrente:
    1. Estrai feature demografiche
    2. Estrai feature cliniche (condizioni, farmaci, procedure)
    3. Estrai feature storiche (ricoveri precedenti)
    4. Estrai parametri vitali
    5. Estrai feature temporali
    6. Estrai feature lab
    7. Calcola target variables

    Returns:
        DataFrame con una riga per encounter, colonne = feature + target
    """
    # Filtra encounter inpatient correnti
    current_encounters = filter_inpatient_encounters(encounters_meta_df)
    print(f"\nEncounters inpatient correnti: {len(current_encounters)}")

    rows = []
    errors = 0

    for idx, enc_row in current_encounters.iterrows():
        patient_id = enc_row['Patient']
        encounter_id = enc_row['Id']

        try:
            enc_start = pd.to_datetime(enc_row['Start'], utc=True).tz_localize(None)
            enc_stop_raw = enc_row.get('Stop', None)
            if enc_stop_raw and str(enc_stop_raw).strip():
                enc_stop = pd.to_datetime(enc_stop_raw, utc=True).tz_localize(None)
            else:
                enc_stop = pd.NaT

            # Reparto (se disponibile dai metadati)
            department = enc_row.get('_department', 'Medicina Interna')

            # 1. Demografiche
            demo = extract_demographics(patients_df, patient_id, enc_start)

            # 2. Cliniche
            clinical = extract_clinical_features(
                conditions_df, medications_df, procedures_df,
                patient_id, enc_start
            )

            # 3. Storiche
            historical = extract_historical_features(
                encounters_meta_df, patient_id, encounter_id, enc_start
            )

            # 4. Vitali
            vitals = extract_vital_signs(observations_df, patient_id, encounter_id)

            # 5. Temporali
            temporal = extract_temporal_features(enc_start)

            # 6. Lab
            lab = extract_lab_features(observations_df, patient_id, enc_start)

            # Combina tutte le feature
            features = {
                'patient_id': patient_id,
                'encounter_id': encounter_id,
                'department': department,
            }
            features.update(demo)
            features.update(clinical)
            features.update(historical)
            features.update(vitals)
            features.update(temporal)
            features.update(lab)

            # 7. Calcola target variables
            # Risk score (formula base)
            features['risk_score'] = compute_base_risk_score(features)

            # Length of Stay
            los = compute_los_days(enc_start, enc_stop)
            if los is None:
                # Paziente ancora ricoverato: stima LOS basata sul profilo
                days_so_far = (pd.Timestamp.now() - enc_start).total_seconds() / 86400
                los = max(1.0, round(days_so_far * 1.3, 1))  # Stima conservativa
            features['los_days'] = los

            # Readmission 30 giorni
            # Calcolo basato sullo storico reale
            readmission_real = compute_readmission_30d(
                encounters_meta_df, patient_id, enc_stop if pd.notna(enc_stop) else enc_start
            )
            if readmission_real == 1:
                features['readmission_30d'] = 1
            else:
                # Per dati sintetici: simula readmission basata sul risk score
                # Pazienti ad alto rischio hanno più probabilità di essere riospedalizzati
                rs = features['risk_score']
                readmission_prob = 0.05 + (rs / 100) * 0.35  # 5-40% in base al risk score
                features['readmission_30d'] = 1 if np.random.random() < readmission_prob else 0

            # Deterioramento
            features['deterioration'] = compute_deterioration(
                encounters_meta_df, encounter_id, patient_id, patients_df
            )

            rows.append(features)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Errore per paziente {patient_id}: {e}")

    if errors > 5:
        print(f"  ... e altri {errors - 5} errori")

    print(f"Feature estratte per {len(rows)} encounters ({errors} errori)")
    return pd.DataFrame(rows)


# =============================================================================
# GESTIONE VALORI MANCANTI
# =============================================================================

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gestisce valori mancanti nel dataset:
    - Feature numeriche: imputa con mediana
    - Assicura che non ci siano NaN nelle colonne ML
    """
    df = df.copy()

    for col in ML_FEATURE_COLUMNS:
        if col in df.columns and df[col].isna().any():
            median_val = df[col].median()
            n_missing = df[col].isna().sum()
            df[col] = df[col].fillna(median_val)
            print(f"  Imputati {n_missing} valori mancanti in '{col}' (mediana: {median_val:.2f})")

    for col in TARGET_COLUMNS:
        if col in df.columns and df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    return df


# =============================================================================
# VALIDAZIONE
# =============================================================================

def validate_dataset(df: pd.DataFrame) -> bool:
    """
    Verifica integrità del dataset finale.

    Returns:
        True se il dataset è valido
    """
    print("\n=== Validazione Dataset ===")
    is_valid = True

    # Controlla che tutte le colonne ML siano presenti
    missing_cols = [c for c in ML_FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        print(f"  ERRORE: colonne mancanti: {missing_cols}")
        is_valid = False
    else:
        print(f"  OK: tutte le {len(ML_FEATURE_COLUMNS)} colonne ML presenti")

    # Controlla NaN
    nan_cols = [c for c in ML_FEATURE_COLUMNS if c in df.columns and df[c].isna().any()]
    if nan_cols:
        print(f"  ERRORE: NaN trovati in: {nan_cols}")
        is_valid = False
    else:
        print("  OK: nessun valore NaN nelle feature")

    # Controlla range risk_score
    if 'risk_score' in df.columns:
        min_rs = df['risk_score'].min()
        max_rs = df['risk_score'].max()
        mean_rs = df['risk_score'].mean()
        print(f"  Risk Score: min={min_rs}, max={max_rs}, media={mean_rs:.1f}")
        if min_rs < 0 or max_rs > 100:
            print("  ERRORE: risk_score fuori range [0, 100]")
            is_valid = False

    # Controlla readmission_30d
    if 'readmission_30d' in df.columns:
        rate = df['readmission_30d'].mean()
        print(f"  Tasso riospedalizzazione 30gg: {rate*100:.1f}%")

    # Controlla los_days
    if 'los_days' in df.columns:
        avg_los = df['los_days'].mean()
        print(f"  Durata media degenza: {avg_los:.1f} giorni")
        if df['los_days'].min() < 0:
            print("  ERRORE: los_days negativo")
            is_valid = False

    # Statistiche demografiche
    if 'age' in df.columns:
        print(f"  Età: min={df['age'].min()}, max={df['age'].max()}, media={df['age'].mean():.1f}")

    if 'gender' in df.columns:
        male_pct = df['gender'].mean() * 100
        print(f"  Genere: {male_pct:.1f}% M, {100-male_pct:.1f}% F")

    # Dimensione dataset
    print(f"  Dimensione: {len(df)} righe x {len(df.columns)} colonne")

    if is_valid:
        print("  VALIDAZIONE COMPLETATA CON SUCCESSO")
    else:
        print("  VALIDAZIONE FALLITA — correggere gli errori sopra")

    return is_valid


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Preprocessa dati Synthea per PatientGuard ML'
    )
    parser.add_argument('--input-dir', type=str, default='data/synthea_output',
                        help='Directory con i CSV Synthea')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                        help='Directory per il dataset ML')
    args = parser.parse_args()

    print("=== PatientGuard — Preprocessing ===\n")

    # 1. Carica CSV
    print("1. Caricamento CSV Synthea...")
    data = load_synthea_csvs(args.input_dir)

    # 2. Costruisci matrice feature
    print("\n2. Estrazione feature...")
    df = build_feature_matrix(
        patients_df=data['patients'],
        encounters_df=data['encounters'],
        encounters_meta_df=data['encounters_meta'],
        conditions_df=data['conditions'],
        medications_df=data['medications'],
        observations_df=data['observations'],
        procedures_df=data['procedures'],
    )

    # 3. Gestisci valori mancanti
    print("\n3. Gestione valori mancanti...")
    df = handle_missing_values(df)

    # 4. Valida
    validate_dataset(df)

    # 5. Salva
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, 'ml_dataset.csv')
    df.to_csv(output_path, index=False)
    print(f"\nDataset salvato in {output_path}")

    # Stampa distribuzione risk score
    if 'risk_score' in df.columns and len(df) > 0:
        print("\nDistribuzione Risk Score:")
        bins = [0, 25, 50, 75, 100]
        labels = ['Basso (1-25)', 'Medio (26-50)', 'Alto (51-75)', 'Critico (76-100)']
        categories = pd.cut(df['risk_score'], bins=bins, labels=labels, include_lowest=True)
        print(categories.value_counts().sort_index().to_string())


if __name__ == '__main__':
    main()
