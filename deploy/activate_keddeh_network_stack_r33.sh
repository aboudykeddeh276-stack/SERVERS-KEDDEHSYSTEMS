#!/usr/bin/env bash
set -euo pipefail

# Accountability wrapper only. The resident activation implementation remains
# deploy/activate_keddeh_network_stack.sh and is executed unchanged after gate
# admission. This wrapper does not promote host/network/public state itself.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVELOPE="${KEX_ACCOUNTABILITY_ENVELOPE:-}"
RECEIPT_OUT="${KEX_ACCOUNTABILITY_CARRIER_RECEIPT:-/var/lib/keddeh/accountability/network-carrier-r33.json}"

if [[ -z "${ENVELOPE}" ]]; then
  echo "ERROR: KEX_ACCOUNTABILITY_ENVELOPE is required" >&2
  exit 40
fi
if [[ ! -r "${ENVELOPE}" ]]; then
  echo "ERROR: accountability envelope unreadable: ${ENVELOPE}" >&2
  exit 41
fi

mkdir -p "$(dirname "${RECEIPT_OUT}")"
python3 "${REPO_ROOT}/governance/network/accountability_carrier_gate_r33.py" "${ENVELOPE}" > "${RECEIPT_OUT}.tmp"
python3 - "${RECEIPT_OUT}.tmp" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
if r.get('state')!='CARRIER_ACTION_ADMITTED':
    raise SystemExit('ACCOUNTABILITY_CARRIER_NOT_ADMITTED')
if r.get('execution_claim')!='NOT_EXECUTED_BY_GATE':
    raise SystemExit('ACCOUNTABILITY_GATE_CLAIM_INFLATION')
if r.get('braink_authority_acquired') is not False:
    raise SystemExit('ACCOUNTABILITY_AUTHORITY_SHIFT_DETECTED')
PY
mv "${RECEIPT_OUT}.tmp" "${RECEIPT_OUT}"

# Preserve and invoke the existing working actuator. Its own host/network/public
# evidence gates remain authoritative for the states it reports.
exec "${REPO_ROOT}/deploy/activate_keddeh_network_stack.sh" "$@"
