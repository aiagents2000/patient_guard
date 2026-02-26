"""
Script di training per i modelli PatientGuard.

Addestra 3 modelli XGBoost e salva i risultati in backend/ml/models/.

Uso:
    cd patientguard
    python3 -m backend.ml.train --data data/processed/ml_dataset.csv

Modelli:
    1. Risk Score Regressor (XGBRegressor) -> risk_score_model.joblib
    2. Readmission Classifier (XGBClassifier) -> readmission_model.joblib
    3. Length of Stay Regressor (XGBRegressor) -> los_model.joblib

Output aggiuntivo:
    - backend/ml/models/preprocessor.joblib
    - backend/ml/models/feature_importance.json
    - backend/ml/models/training_metrics.json
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Prova XGBoost, fallback su sklearn GradientBoosting
try:
    from xgboost import XGBClassifier, XGBRegressor
    USE_XGBOOST = True
except Exception:
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    USE_XGBOOST = False
    print("XGBoost non disponibile, uso sklearn GradientBoosting come fallback.")

# Aggiungi root al path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.features import FEATURE_DISPLAY_NAMES, ML_FEATURE_COLUMNS
from ml.pipeline import FeaturePreprocessor


# =============================================================================
# CONFIGURAZIONE IPERPARAMETRI
# =============================================================================

RISK_SCORE_PARAMS = {
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse',
    'random_state': 42,
    'n_jobs': -1,
}

READMISSION_PARAMS = {
    'n_estimators': 200,
    'max_depth': 5,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'scale_pos_weight': 3.0,  # Classe sbilanciata
    'random_state': 42,
    'n_jobs': -1,
}

LOS_PARAMS = {
    'n_estimators': 150,
    'max_depth': 5,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'reg:squarederror',
    'eval_metric': 'mae',
    'random_state': 42,
    'n_jobs': -1,
}


# =============================================================================
# FUNZIONI DI TRAINING
# =============================================================================

def load_and_prepare_data(csv_path: str) -> tuple:
    """
    Carica il dataset, separa feature e target, esegue split train/test.

    Returns:
        (X_train, X_test, y_train_dict, y_test_dict, preprocessor, df)
    """
    print(f"Caricamento dataset da {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  Dimensione: {len(df)} righe x {len(df.columns)} colonne")

    # Verifica che tutte le feature ML siano presenti
    missing = [c for c in ML_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonne mancanti nel dataset: {missing}")

    # Separa feature e target
    X = df[ML_FEATURE_COLUMNS]
    targets = {
        'risk_score': df['risk_score'],
        'readmission_30d': df['readmission_30d'],
        'los_days': df['los_days'],
    }

    # Split train/test (80/20, stratificato per readmission)
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.2,
        random_state=42,
        stratify=targets['readmission_30d']
    )

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = {k: v.iloc[train_idx] for k, v in targets.items()}
    y_test = {k: v.iloc[test_idx] for k, v in targets.items()}

    # Preprocessing (scaling)
    preprocessor = FeaturePreprocessor()
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    print(f"  Train: {len(X_train)} campioni")
    print(f"  Test:  {len(X_test)} campioni")

    return X_train_scaled, X_test_scaled, y_train, y_test, preprocessor, df


def train_risk_score_model(X_train: np.ndarray, y_train: np.ndarray,
                           X_test: np.ndarray, y_test: np.ndarray) -> tuple:
    """
    Addestra XGBRegressor per il risk score.

    Returns:
        (modello, dizionario metriche)
    """
    print("\n--- Training: Risk Score Regressor ---")
    if USE_XGBOOST:
        model = XGBRegressor(**RISK_SCORE_PARAMS)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    else:
        model = GradientBoostingRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, random_state=42
        )
        model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    # Clamp predizioni nel range 1-99
    y_pred = np.clip(y_pred, 1, 99)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {'rmse': round(rmse, 2), 'mae': round(mae, 2), 'r2': round(r2, 4)}
    print(f"  RMSE: {rmse:.2f}")
    print(f"  MAE:  {mae:.2f}")
    print(f"  R²:   {r2:.4f}")

    return model, metrics


def train_readmission_model(X_train: np.ndarray, y_train: np.ndarray,
                             X_test: np.ndarray, y_test: np.ndarray) -> tuple:
    """
    Addestra XGBClassifier per readmission a 30 giorni.

    Returns:
        (modello, dizionario metriche)
    """
    print("\n--- Training: Readmission Classifier ---")
    if USE_XGBOOST:
        model = XGBClassifier(**READMISSION_PARAMS)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    else:
        model = GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            subsample=0.8, random_state=42
        )
        model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc = float(roc_auc_score(y_test, y_pred_proba))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    metrics = {
        'auc_roc': round(auc, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
    }
    print(f"  AUC-ROC:   {auc:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")

    return model, metrics


def train_los_model(X_train: np.ndarray, y_train: np.ndarray,
                    X_test: np.ndarray, y_test: np.ndarray) -> tuple:
    """
    Addestra XGBRegressor per Length of Stay.

    Returns:
        (modello, dizionario metriche)
    """
    print("\n--- Training: Length of Stay Regressor ---")
    if USE_XGBOOST:
        model = XGBRegressor(**LOS_PARAMS)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    else:
        model = GradientBoostingRegressor(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            subsample=0.8, random_state=42
        )
        model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred = np.maximum(y_pred, 0.5)  # Minimo mezzo giorno

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {'rmse': round(rmse, 2), 'mae': round(mae, 2), 'r2': round(r2, 4)}
    print(f"  RMSE: {rmse:.2f}")
    print(f"  MAE:  {mae:.2f}")
    print(f"  R²:   {r2:.4f}")

    return model, metrics


# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

def compute_feature_importance(risk_model, readmission_model, los_model,
                                feature_names: list[str]) -> dict:
    """
    Calcola feature importance aggregata dai 3 modelli.
    Usa XGBoost native feature_importances_ (gain-based).

    Returns:
        dict con importance per feature e per modello
    """
    importance = {}

    for name, model in [('risk_score', risk_model),
                         ('readmission', readmission_model),
                         ('los', los_model)]:
        fi = model.feature_importances_

        for idx, feature in enumerate(feature_names):
            if feature not in importance:
                importance[feature] = {
                    'display_name': FEATURE_DISPLAY_NAMES.get(feature, feature),
                    'models': {},
                }
            importance[feature]['models'][name] = round(float(fi[idx]), 6)

    # Calcola importanza media
    for feature in importance:
        model_values = list(importance[feature]['models'].values())
        importance[feature]['overall'] = round(float(np.mean(model_values)), 6)

    # Ordina per importanza media decrescente
    importance = dict(sorted(
        importance.items(),
        key=lambda x: x[1]['overall'],
        reverse=True
    ))

    return importance


# =============================================================================
# SALVATAGGIO
# =============================================================================

def save_all(risk_model, readmission_model, los_model,
             preprocessor: FeaturePreprocessor,
             feature_importance: dict,
             metrics: dict,
             output_dir: str) -> None:
    """Salva tutti i modelli e gli artefatti."""
    os.makedirs(output_dir, exist_ok=True)

    # Modelli
    joblib.dump(risk_model, os.path.join(output_dir, 'risk_score_model.joblib'))
    print(f"  Salvato risk_score_model.joblib")

    joblib.dump(readmission_model, os.path.join(output_dir, 'readmission_model.joblib'))
    print(f"  Salvato readmission_model.joblib")

    joblib.dump(los_model, os.path.join(output_dir, 'los_model.joblib'))
    print(f"  Salvato los_model.joblib")

    # Preprocessore
    preprocessor.save(os.path.join(output_dir, 'preprocessor.joblib'))

    # Feature importance
    fi_path = os.path.join(output_dir, 'feature_importance.json')
    with open(fi_path, 'w', encoding='utf-8') as f:
        json.dump(feature_importance, f, indent=2, ensure_ascii=False)
    print(f"  Salvato feature_importance.json")

    # Metriche di training
    metrics_path = os.path.join(output_dir, 'training_metrics.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"  Salvato training_metrics.json")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Training modelli PatientGuard')
    parser.add_argument('--data', type=str, default='data/processed/ml_dataset.csv',
                        help='Path al dataset ML preprocessato')
    parser.add_argument('--output-dir', type=str, default='backend/ml/models',
                        help='Directory per salvare i modelli')
    args = parser.parse_args()

    print("=== PatientGuard — Training Modelli ML ===\n")

    # 1. Carica e prepara dati
    X_train, X_test, y_train, y_test, preprocessor, df = load_and_prepare_data(args.data)

    # 2. Training dei 3 modelli
    risk_model, risk_metrics = train_risk_score_model(
        X_train, y_train['risk_score'].values,
        X_test, y_test['risk_score'].values
    )

    readmission_model, readmission_metrics = train_readmission_model(
        X_train, y_train['readmission_30d'].values,
        X_test, y_test['readmission_30d'].values
    )

    los_model, los_metrics = train_los_model(
        X_train, y_train['los_days'].values,
        X_test, y_test['los_days'].values
    )

    # 3. Feature importance
    print("\n--- Feature Importance ---")
    feature_importance = compute_feature_importance(
        risk_model, readmission_model, los_model,
        ML_FEATURE_COLUMNS
    )

    # Stampa top 10
    print("  Top 10 feature (importanza media):")
    for i, (feature, data) in enumerate(feature_importance.items()):
        if i >= 10:
            break
        display = data['display_name']
        overall = data['overall']
        print(f"    {i+1}. {display} ({feature}): {overall:.4f}")

    # 4. Salvataggio
    all_metrics = {
        'risk_score': risk_metrics,
        'readmission': readmission_metrics,
        'los': los_metrics,
        'dataset': {
            'total_samples': len(df),
            'train_samples': X_train.shape[0],
            'test_samples': X_test.shape[0],
            'n_features': len(ML_FEATURE_COLUMNS),
            'readmission_rate': round(float(df['readmission_30d'].mean()), 4),
        }
    }

    print(f"\n--- Salvataggio in {args.output_dir}/ ---")
    save_all(
        risk_model, readmission_model, los_model,
        preprocessor, feature_importance, all_metrics,
        args.output_dir
    )

    # 5. Riepilogo
    print("\n=== TRAINING COMPLETATO ===")
    print(f"  Risk Score:   RMSE={risk_metrics['rmse']}, R²={risk_metrics['r2']}")
    print(f"  Readmission:  AUC={readmission_metrics['auc_roc']}, F1={readmission_metrics['f1']}")
    print(f"  LOS:          MAE={los_metrics['mae']}, R²={los_metrics['r2']}")


if __name__ == '__main__':
    main()
