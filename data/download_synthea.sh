#!/bin/bash
# Script wrapper: genera dati sintetici usando il generatore Python
# Alternativa a Synthea Java per evitare la dipendenza da Java
# I CSV generati hanno lo stesso formato di Synthea reale

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUM_PATIENTS=${1:-1000}

echo "=== PatientGuard — Generatore Dati Sintetici ==="
echo "Generazione di ${NUM_PATIENTS} pazienti sintetici..."
echo ""

python3 "${SCRIPT_DIR}/generate_synthea.py" \
    --num-patients "${NUM_PATIENTS}" \
    --output-dir "${SCRIPT_DIR}/synthea_output"

echo ""
echo "Fatto! I CSV sono in ${SCRIPT_DIR}/synthea_output/"
