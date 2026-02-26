-- =============================================================================
-- PatientGuard — Schema PostgreSQL per Supabase
-- =============================================================================
-- Eseguire in Supabase SQL Editor per creare le tabelle.
-- Compatibile con Supabase (PostgreSQL 15+).
-- =============================================================================

-- Pazienti
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    fiscal_code VARCHAR(16),
    department VARCHAR(100) NOT NULL,
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Condizioni / Diagnosi
CREATE TABLE IF NOT EXISTS conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    icd10_code VARCHAR(10),
    description VARCHAR(255) NOT NULL,
    onset_date DATE,
    is_active BOOLEAN DEFAULT true
);

-- Farmaci
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true
);

-- Parametri vitali (time series)
CREATE TABLE IF NOT EXISTS vitals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    spo2 DECIMAL(4,1),
    temperature DECIMAL(3,1),
    glucose INTEGER,
    creatinine DECIMAL(4,2),
    hemoglobin DECIMAL(4,1)
);

-- Esami di laboratorio
CREATE TABLE IF NOT EXISTS lab_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    test_name VARCHAR(100) NOT NULL,
    value DECIMAL(10,2),
    unit VARCHAR(20),
    reference_range VARCHAR(50),
    is_abnormal BOOLEAN DEFAULT false,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Note cliniche
CREATE TABLE IF NOT EXISTS clinical_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    author VARCHAR(100),
    note_type VARCHAR(50),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Predizioni ML (storico)
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    readmission_prob DECIMAL(5,4),
    predicted_los DECIMAL(5,1),
    risk_factors JSONB,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alert
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ricoveri precedenti
CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    encounter_type VARCHAR(50),
    department VARCHAR(100),
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,
    los_days INTEGER,
    discharge_disposition VARCHAR(100)
);

-- =============================================================================
-- INDICI
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_conditions_patient ON conditions(patient_id);
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_vitals_patient_ts ON vitals(patient_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_patient_ts ON predictions(patient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_patient ON alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_patients_department ON patients(department);
CREATE INDEX IF NOT EXISTS idx_patients_active ON patients(is_active);

-- =============================================================================
-- ROW LEVEL SECURITY (opzionale, da abilitare in produzione)
-- =============================================================================
-- ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conditions ENABLE ROW LEVEL SECURITY;
-- etc.
