"""
Livello di accesso dati per PatientGuard.

Dual-mode:
- Supabase: quando SUPABASE_URL e SUPABASE_KEY sono configurati
- JSON Demo: fallback su data/sample/synthetic_patients.json

Il DataStore astratto garantisce che i router funzionino in entrambi i casi.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import Settings, get_settings


# =============================================================================
# DATA STORE INTERFACE
# =============================================================================

class DataStore:
    """Interfaccia unificata per l'accesso ai dati."""

    async def get_patients(
        self,
        department: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        raise NotImplementedError

    async def get_patient(self, patient_id: str) -> Optional[dict]:
        raise NotImplementedError

    async def get_patient_vitals(self, patient_id: str, limit: int = 50) -> list[dict]:
        raise NotImplementedError

    async def get_patient_predictions(self, patient_id: str, limit: int = 30) -> list[dict]:
        raise NotImplementedError

    async def get_patient_record(self, patient_id: str) -> Optional[dict]:
        raise NotImplementedError

    async def save_prediction(self, patient_id: str, prediction: dict) -> dict:
        raise NotImplementedError

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
    ) -> list[dict]:
        raise NotImplementedError

    async def mark_alert_read(self, alert_id: str) -> Optional[dict]:
        raise NotImplementedError

    async def mark_alert_resolved(self, alert_id: str) -> Optional[dict]:
        raise NotImplementedError

    async def create_alert(self, alert: dict) -> dict:
        raise NotImplementedError

    async def get_stats_overview(self) -> dict:
        raise NotImplementedError

    async def get_stats_department(self) -> list[dict]:
        raise NotImplementedError

    async def get_patient_features(self, patient_id: str) -> Optional[dict]:
        """Restituisce le feature ML per un paziente (per predict)."""
        raise NotImplementedError

    async def get_patient_notes(self, patient_id: str) -> list[dict]:
        raise NotImplementedError


# =============================================================================
# JSON DEMO STORE
# =============================================================================

class JsonDemoStore(DataStore):
    """
    DataStore che legge da synthetic_patients.json.
    Tiene i dati in memoria e supporta operazioni di scrittura in-memory
    (alert, predizioni) che si perdono al restart — sufficiente per la demo.
    """

    def __init__(self, json_path: str):
        self._path = Path(json_path)
        self._patients: list[dict] = []
        self._alerts: list[dict] = []
        self._extra_predictions: dict[str, list[dict]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            print(f"WARN: JSON demo non trovato: {self._path}")
            return
        with open(self._path, 'r', encoding='utf-8') as f:
            self._patients = json.load(f)
        print(f"JsonDemoStore: caricati {len(self._patients)} pazienti da {self._path}")

        # Genera alert iniziali per pazienti ad alto rischio
        for p in self._patients:
            pred = p.get('prediction', {})
            if pred.get('risk_level') in ('critico', 'alto'):
                self._alerts.append({
                    'id': str(uuid.uuid4()),
                    'patient_id': p['id'],
                    'patient_name': p.get('name', ''),
                    'alert_type': 'risk_increase' if pred.get('risk_level') == 'critico' else 'readmission_warning',
                    'severity': 'critical' if pred.get('risk_level') == 'critico' else 'high',
                    'message': self._generate_alert_message(p),
                    'is_read': False,
                    'is_resolved': False,
                    'created_at': datetime.now().isoformat(),
                })

            # Alert per vitali critici
            vitals = p.get('vitals', {})
            critical_msgs = []
            if vitals.get('systolic_bp', 0) > 180:
                critical_msgs.append(f"PA sistolica {vitals['systolic_bp']} mmHg")
            if vitals.get('systolic_bp', 999) < 80:
                critical_msgs.append(f"PA sistolica {vitals['systolic_bp']} mmHg (ipotensione)")
            if vitals.get('spo2', 100) < 90:
                critical_msgs.append(f"SpO2 {vitals['spo2']}%")
            if vitals.get('heart_rate', 0) > 120:
                critical_msgs.append(f"FC {vitals['heart_rate']} bpm (tachicardia)")
            if vitals.get('heart_rate', 999) < 40:
                critical_msgs.append(f"FC {vitals['heart_rate']} bpm (bradicardia)")
            if vitals.get('temperature', 0) > 39:
                critical_msgs.append(f"Temperatura {vitals['temperature']}°C")
            if vitals.get('glucose', 0) > 300:
                critical_msgs.append(f"Glicemia {vitals['glucose']} mg/dL")
            if vitals.get('glucose', 999) < 50:
                critical_msgs.append(f"Glicemia {vitals['glucose']} mg/dL (ipoglicemia)")

            if critical_msgs:
                self._alerts.append({
                    'id': str(uuid.uuid4()),
                    'patient_id': p['id'],
                    'patient_name': p.get('name', ''),
                    'alert_type': 'critical_vitals',
                    'severity': 'critical',
                    'message': f"Parametri vitali critici: {', '.join(critical_msgs)}",
                    'is_read': False,
                    'is_resolved': False,
                    'created_at': datetime.now().isoformat(),
                })

    @staticmethod
    def _generate_alert_message(patient: dict) -> str:
        pred = patient.get('prediction', {})
        name = patient.get('name', 'Paziente')
        dept = patient.get('department', '')
        score = pred.get('risk_score', 0)
        level = pred.get('risk_level', '')
        if level == 'critico':
            return (f"{name} ({dept}): risk score {score}/100 — livello CRITICO. "
                    f"Probabilità riospedalizzazione {pred.get('readmission_probability', 0)*100:.0f}%.")
        return (f"{name} ({dept}): risk score {score}/100 — livello ALTO. "
                f"Monitorare attentamente.")

    # --- Pazienti ---

    async def get_patients(self, department=None, risk_level=None,
                           search=None, is_active=None, limit=50, offset=0):
        results = self._patients
        if department:
            results = [p for p in results if p.get('department') == department]
        if risk_level:
            results = [p for p in results
                       if p.get('prediction', {}).get('risk_level') == risk_level]
        if search:
            q = search.lower()
            results = [p for p in results
                       if q in p.get('name', '').lower()
                       or q in p.get('fiscal_code', '').lower()
                       or q in p.get('id', '').lower()]
        if is_active is not None:
            results = [p for p in results if p.get('is_active') == is_active]
        return results[offset:offset + limit]

    async def get_patient(self, patient_id: str):
        for p in self._patients:
            if p['id'] == patient_id:
                return p
        return None

    async def get_patient_vitals(self, patient_id: str, limit=50):
        p = await self.get_patient(patient_id)
        if not p:
            return []
        vitals = p.get('vitals', {})
        # Restituisce il punto attuale; nel DB reale sarebbe una serie temporale
        return [{'timestamp': datetime.now().isoformat(), **vitals}]

    async def get_patient_predictions(self, patient_id: str, limit=30):
        p = await self.get_patient(patient_id)
        if not p:
            return []
        # Usa risk_trend come storico predizioni
        trend = p.get('risk_trend', [])
        extra = self._extra_predictions.get(patient_id, [])
        results = []
        for t in trend:
            results.append({
                'date': t['date'],
                'risk_score': t['score'],
                'model_version': '1.0.0',
            })
        results.extend(extra)
        return results[-limit:]

    async def get_patient_record(self, patient_id: str):
        p = await self.get_patient(patient_id)
        if not p:
            return None
        return {
            'conditions': p.get('conditions', []),
            'medications': p.get('medications', []),
            'vitals': p.get('vitals', {}),
            'clinical_notes': p.get('clinical_notes', []),
            'encounters_history': p.get('encounters_history', []),
        }

    async def save_prediction(self, patient_id: str, prediction: dict):
        entry = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'created_at': datetime.now().isoformat(),
            **prediction,
        }
        self._extra_predictions.setdefault(patient_id, []).append(entry)

        # Aggiorna anche la predizione corrente del paziente in memoria
        for p in self._patients:
            if p['id'] == patient_id:
                p['prediction'] = prediction
                break
        return entry

    async def get_patient_features(self, patient_id: str):
        """Ricostruisce le feature ML dal record paziente JSON."""
        p = await self.get_patient(patient_id)
        if not p:
            return None
        vitals = p.get('vitals', {})
        pred = p.get('prediction', {})
        return {
            'patient_id': p['id'],
            'age': p.get('age', 0),
            'gender': 1 if p.get('gender') == 'M' else 0,
            'n_active_conditions': len(p.get('conditions', [])),
            'n_active_medications': len(p.get('medications', [])),
            'systolic_bp': vitals.get('systolic_bp', 120),
            'diastolic_bp': vitals.get('diastolic_bp', 75),
            'heart_rate': vitals.get('heart_rate', 75),
            'spo2': vitals.get('spo2', 97),
            'temperature': vitals.get('temperature', 36.6),
            'glucose': vitals.get('glucose', 100),
            'creatinine': vitals.get('creatinine', 1.0),
            'hemoglobin': vitals.get('hemoglobin', 13.0),
            'department': p.get('department', 'Medicina Interna'),
            # Feature storiche — stimate dal JSON
            'admissions_last_12m': len(p.get('encounters_history', [])),
            'admissions_last_6m': len([e for e in p.get('encounters_history', [])
                                        if e.get('type') == 'inpatient']),
            'days_since_last_admission': 30,
            'avg_los_previous': sum(e.get('los_days', 5) for e in p.get('encounters_history', [1])) / max(1, len(p.get('encounters_history', [1]))),
            'n_procedures': 0,
            'has_heart_failure': any('heart failure' in c.get('description', '').lower() for c in p.get('conditions', [])),
            'has_copd': any('copd' in c.get('description', '').lower() for c in p.get('conditions', [])),
            'has_diabetes': any('diabetes' in c.get('description', '').lower() for c in p.get('conditions', [])),
            'has_ckd': any('kidney' in c.get('description', '').lower() for c in p.get('conditions', [])),
            'has_hypertension': any('hypertension' in c.get('description', '').lower() for c in p.get('conditions', [])),
            'admission_hour': 10,
            'admission_weekend': 0,
        }

    async def get_patient_notes(self, patient_id: str):
        p = await self.get_patient(patient_id)
        if not p:
            return []
        return p.get('clinical_notes', [])

    # --- Alert ---

    async def get_alerts(self, severity=None, is_read=None, limit=50):
        results = self._alerts
        if severity:
            results = [a for a in results if a.get('severity') == severity]
        if is_read is not None:
            results = [a for a in results if a.get('is_read') == is_read]
        # Più recenti prima
        results = sorted(results, key=lambda a: a.get('created_at', ''), reverse=True)
        return results[:limit]

    async def mark_alert_read(self, alert_id: str):
        for a in self._alerts:
            if a['id'] == alert_id:
                a['is_read'] = True
                return a
        return None

    async def mark_alert_resolved(self, alert_id: str):
        for a in self._alerts:
            if a['id'] == alert_id:
                a['is_resolved'] = True
                return a
        return None

    async def create_alert(self, alert: dict):
        entry = {
            'id': str(uuid.uuid4()),
            'is_read': False,
            'is_resolved': False,
            'created_at': datetime.now().isoformat(),
            **alert,
        }
        self._alerts.insert(0, entry)
        return entry

    # --- Stats ---

    async def get_stats_overview(self):
        total = len(self._patients)
        active = sum(1 for p in self._patients if p.get('is_active'))
        scores = [p.get('prediction', {}).get('risk_score', 0) for p in self._patients]
        avg_score = sum(scores) / max(1, len(scores))
        distribution = {'basso': 0, 'medio': 0, 'alto': 0, 'critico': 0}
        for p in self._patients:
            level = p.get('prediction', {}).get('risk_level', 'basso')
            distribution[level] = distribution.get(level, 0) + 1
        active_alerts = sum(1 for a in self._alerts if not a.get('is_resolved'))
        return {
            'total_patients': total,
            'active_patients': active,
            'avg_risk_score': round(avg_score, 1),
            'risk_distribution': distribution,
            'active_alerts': active_alerts,
        }

    async def get_stats_department(self):
        dept_data: dict[str, list] = {}
        for p in self._patients:
            dept = p.get('department', 'Altro')
            dept_data.setdefault(dept, []).append(p)
        results = []
        for dept, patients in dept_data.items():
            scores = [p.get('prediction', {}).get('risk_score', 0) for p in patients]
            results.append({
                'department': dept,
                'patient_count': len(patients),
                'avg_risk_score': round(sum(scores) / max(1, len(scores)), 1),
                'critical_count': sum(1 for p in patients
                                      if p.get('prediction', {}).get('risk_level') == 'critico'),
                'high_count': sum(1 for p in patients
                                  if p.get('prediction', {}).get('risk_level') == 'alto'),
            })
        results.sort(key=lambda x: x['avg_risk_score'], reverse=True)
        return results


# =============================================================================
# SUPABASE STORE
# =============================================================================

class SupabaseStore(DataStore):
    """DataStore backed da Supabase PostgreSQL."""

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.client = create_client(url, key)
        print(f"SupabaseStore: connesso a {url}")

    async def get_patients(self, department=None, risk_level=None,
                           search=None, is_active=None, limit=50, offset=0):
        query = self.client.table('patients').select(
            '*, predictions!predictions_patient_id_fkey(risk_score, readmission_prob, '
            'predicted_los, risk_factors, model_version, created_at)'
        )
        if department:
            query = query.eq('department', department)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        if search:
            query = query.or_(f"name.ilike.%{search}%,fiscal_code.ilike.%{search}%")
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        patients = result.data or []

        # Filtra per risk_level lato client (calcolato dalla predizione)
        if risk_level:
            patients = [p for p in patients if self._calc_risk_level(p) == risk_level]
        return patients

    async def get_patient(self, patient_id: str):
        result = (self.client.table('patients')
                  .select('*')
                  .eq('id', patient_id)
                  .single()
                  .execute())
        return result.data

    async def get_patient_vitals(self, patient_id: str, limit=50):
        result = (self.client.table('vitals')
                  .select('*')
                  .eq('patient_id', patient_id)
                  .order('timestamp', desc=True)
                  .limit(limit)
                  .execute())
        return result.data or []

    async def get_patient_predictions(self, patient_id: str, limit=30):
        result = (self.client.table('predictions')
                  .select('*')
                  .eq('patient_id', patient_id)
                  .order('created_at', desc=True)
                  .limit(limit)
                  .execute())
        return result.data or []

    async def get_patient_record(self, patient_id: str):
        conditions = (self.client.table('conditions')
                      .select('*').eq('patient_id', patient_id).execute()).data or []
        medications = (self.client.table('medications')
                       .select('*').eq('patient_id', patient_id).execute()).data or []
        vitals = (self.client.table('vitals')
                  .select('*').eq('patient_id', patient_id)
                  .order('timestamp', desc=True).limit(1).execute()).data
        notes = (self.client.table('clinical_notes')
                 .select('*').eq('patient_id', patient_id)
                 .order('timestamp', desc=True).execute()).data or []
        encounters = (self.client.table('encounters')
                      .select('*').eq('patient_id', patient_id)
                      .order('admission_date', desc=True).execute()).data or []
        return {
            'conditions': conditions,
            'medications': medications,
            'vitals': vitals[0] if vitals else {},
            'clinical_notes': notes,
            'encounters_history': encounters,
        }

    async def save_prediction(self, patient_id: str, prediction: dict):
        data = {'patient_id': patient_id, **prediction}
        result = self.client.table('predictions').insert(data).execute()
        return result.data[0] if result.data else data

    async def get_patient_features(self, patient_id: str):
        patient = await self.get_patient(patient_id)
        if not patient:
            return None
        vitals_list = await self.get_patient_vitals(patient_id, limit=1)
        vitals = vitals_list[0] if vitals_list else {}
        conditions = (self.client.table('conditions')
                      .select('description, is_active')
                      .eq('patient_id', patient_id)
                      .eq('is_active', True).execute()).data or []
        medications = (self.client.table('medications')
                       .select('name, is_active')
                       .eq('patient_id', patient_id)
                       .eq('is_active', True).execute()).data or []
        encounters = (self.client.table('encounters')
                      .select('*').eq('patient_id', patient_id).execute()).data or []

        return {
            'patient_id': patient_id,
            'age': patient.get('age', 0),
            'gender': 1 if patient.get('gender') == 'M' else 0,
            'n_active_conditions': len(conditions),
            'n_active_medications': len(medications),
            'systolic_bp': vitals.get('systolic_bp', 120),
            'diastolic_bp': vitals.get('diastolic_bp', 75),
            'heart_rate': vitals.get('heart_rate', 75),
            'spo2': vitals.get('spo2', 97),
            'temperature': vitals.get('temperature', 36.6),
            'glucose': vitals.get('glucose', 100),
            'creatinine': vitals.get('creatinine', 1.0),
            'hemoglobin': vitals.get('hemoglobin', 13.0),
            'department': patient.get('department', 'Medicina Interna'),
            'admissions_last_12m': len(encounters),
            'admissions_last_6m': len(encounters),
            'days_since_last_admission': 30,
            'avg_los_previous': 5.0,
            'n_procedures': 0,
            'has_heart_failure': any('heart failure' in c.get('description', '').lower() for c in conditions),
            'has_copd': any('copd' in c.get('description', '').lower() for c in conditions),
            'has_diabetes': any('diabetes' in c.get('description', '').lower() for c in conditions),
            'has_ckd': any('kidney' in c.get('description', '').lower() for c in conditions),
            'has_hypertension': any('hypertension' in c.get('description', '').lower() for c in conditions),
            'admission_hour': 10,
            'admission_weekend': 0,
        }

    async def get_patient_notes(self, patient_id: str):
        result = (self.client.table('clinical_notes')
                  .select('*').eq('patient_id', patient_id)
                  .order('timestamp', desc=True).execute())
        return result.data or []

    # --- Alert ---

    async def get_alerts(self, severity=None, is_read=None, limit=50):
        query = self.client.table('alerts').select('*')
        if severity:
            query = query.eq('severity', severity)
        if is_read is not None:
            query = query.eq('is_read', is_read)
        query = query.order('created_at', desc=True).limit(limit)
        result = query.execute()
        return result.data or []

    async def mark_alert_read(self, alert_id: str):
        result = (self.client.table('alerts')
                  .update({'is_read': True})
                  .eq('id', alert_id).execute())
        return result.data[0] if result.data else None

    async def mark_alert_resolved(self, alert_id: str):
        result = (self.client.table('alerts')
                  .update({'is_resolved': True})
                  .eq('id', alert_id).execute())
        return result.data[0] if result.data else None

    async def create_alert(self, alert: dict):
        result = self.client.table('alerts').insert(alert).execute()
        return result.data[0] if result.data else alert

    # --- Stats ---

    async def get_stats_overview(self):
        patients = (self.client.table('patients').select('id, is_active').execute()).data or []
        total = len(patients)
        active = sum(1 for p in patients if p.get('is_active'))
        alerts = (self.client.table('alerts')
                  .select('id').eq('is_resolved', False).execute()).data or []
        # Per le statistiche aggregate, serve una query sulle predictions
        preds = (self.client.table('predictions')
                 .select('risk_score, patient_id')
                 .order('created_at', desc=True).execute()).data or []
        # Prendi l'ultima predizione per paziente
        latest: dict[str, int] = {}
        for p in preds:
            pid = p['patient_id']
            if pid not in latest:
                latest[pid] = p['risk_score']
        scores = list(latest.values())
        avg_score = sum(scores) / max(1, len(scores))
        distribution = {'basso': 0, 'medio': 0, 'alto': 0, 'critico': 0}
        for s in scores:
            if s <= 25:
                distribution['basso'] += 1
            elif s <= 50:
                distribution['medio'] += 1
            elif s <= 75:
                distribution['alto'] += 1
            else:
                distribution['critico'] += 1
        return {
            'total_patients': total,
            'active_patients': active,
            'avg_risk_score': round(avg_score, 1),
            'risk_distribution': distribution,
            'active_alerts': len(alerts),
        }

    async def get_stats_department(self):
        patients = (self.client.table('patients')
                    .select('id, department').execute()).data or []
        dept_ids: dict[str, list[str]] = {}
        for p in patients:
            dept_ids.setdefault(p['department'], []).append(p['id'])
        results = []
        for dept, ids in dept_ids.items():
            results.append({
                'department': dept,
                'patient_count': len(ids),
                'avg_risk_score': 0,
                'critical_count': 0,
                'high_count': 0,
            })
        return results

    @staticmethod
    def _calc_risk_level(patient: dict) -> str:
        preds = patient.get('predictions', [])
        if not preds:
            return 'basso'
        score = preds[0].get('risk_score', 0)
        if score <= 25:
            return 'basso'
        elif score <= 50:
            return 'medio'
        elif score <= 75:
            return 'alto'
        return 'critico'


# =============================================================================
# FACTORY
# =============================================================================

_store_instance: Optional[DataStore] = None


def get_datastore() -> DataStore:
    """Restituisce il DataStore singleton (Supabase o JSON demo)."""
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    settings = get_settings()
    if settings.use_supabase:
        _store_instance = SupabaseStore(settings.supabase_url, settings.supabase_key)
    else:
        print("Supabase non configurato — uso JSON demo mode")
        _store_instance = JsonDemoStore(settings.demo_json_path)
    return _store_instance
