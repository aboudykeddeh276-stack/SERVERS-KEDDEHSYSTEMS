#!/usr/bin/env bash
set -euo pipefail

INSTANCE="${1:-alpha-production}"
SERVER_REPO="${KEDDEH_SERVER_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BRAINK_SOURCE_ROOT="${BRAINK_SOURCE_ROOT:-/opt/keddeh/BRAINK}"
VENV_ROOT="${KEDDEH_SAAS_VENV:-/opt/keddeh/venvs/keddeh-saas}"
STATE_ROOT="${KEDDEH_STATE_ROOT:-/var/lib/keddeh}"
STATE_DIR="${STATE_ROOT}/saas/${INSTANCE}"
ENV_DIR="/etc/keddeh/saas"
ENV_FILE="${ENV_DIR}/${INSTANCE}.env"
SERVICE_SRC="${SERVER_REPO}/runtime/saas/systemd/keddeh-saas-control-plane@.service"
SERVICE_DST="/etc/systemd/system/keddeh-saas-control-plane@.service"
EXAMPLE_ENV="${SERVER_REPO}/runtime/saas/config/saas.env.example"
SERVICE_SOURCE="${BRAINK_SOURCE_ROOT}/services/keddeh-saas-control-plane"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 2
fi

for cmd in python3 systemctl install; do
  command -v "${cmd}" >/dev/null || { echo "ERROR: ${cmd} missing" >&2; exit 3; }
done

for required in \
  "${BRAINK_SOURCE_ROOT}/runtime/illlm_ledger.py" \
  "${BRAINK_SOURCE_ROOT}/runtime/runtime_registry.py" \
  "${SERVICE_SOURCE}/pyproject.toml" \
  "${SERVICE_SOURCE}/src/keddeh_saas/app.py" \
  "${SERVICE_SRC}" \
  "${EXAMPLE_ENV}"; do
  [[ -f "${required}" ]] || { echo "ERROR: required source missing: ${required}" >&2; exit 4; }
done

if ! id keddeh >/dev/null 2>&1; then
  useradd --system --home-dir /opt/keddeh --create-home --shell /usr/sbin/nologin keddeh
fi

mkdir -p "${STATE_DIR}" "${STATE_DIR}/braink" "${ENV_DIR}" "$(dirname "${VENV_ROOT}")"
chown -R keddeh:keddeh "${STATE_DIR}"
chmod 0750 "${STATE_ROOT}" "${STATE_ROOT}/saas" "${STATE_DIR}" "${STATE_DIR}/braink" 2>/dev/null || true

if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  python3 -m venv "${VENV_ROOT}"
fi

PIP=("${VENV_ROOT}/bin/python" -m pip)
if [[ -n "${KEDDEH_WHEELHOUSE:-}" ]]; then
  [[ -d "${KEDDEH_WHEELHOUSE}" ]] || { echo "ERROR: KEDDEH_WHEELHOUSE is not a directory" >&2; exit 5; }
  "${PIP[@]}" install --no-index --find-links "${KEDDEH_WHEELHOUSE}" "${SERVICE_SOURCE}"
else
  "${PIP[@]}" install "${SERVICE_SOURCE}"
fi

install -m 0644 "${SERVICE_SRC}" "${SERVICE_DST}"

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0600 "${EXAMPLE_ENV}" "${ENV_FILE}"
  sed -i "s#INSTANCE#${INSTANCE}#g" "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Bind KEDDEH_CONTROL_API_KEY before activation." >&2
  systemctl daemon-reload
  echo "SERVICE_NOT_STARTED_CONFIG_REQUIRED"
  exit 10
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

[[ -n "${KEDDEH_CONTROL_API_KEY:-}" && "${KEDDEH_CONTROL_API_KEY}" != "REPLACE_ON_HOST" ]] || {
  echo "ERROR: KEDDEH_CONTROL_API_KEY unbound" >&2
  exit 11
}

[[ "${KEDDEH_SAAS_DB:-}" == "${STATE_DIR}"/* ]] || {
  echo "ERROR: KEDDEH_SAAS_DB must remain under ${STATE_DIR}" >&2
  exit 12
}
[[ "${BRAINK_SAAS_STATE_DIR:-}" == "${STATE_DIR}"/* ]] || {
  echo "ERROR: BRAINK_SAAS_STATE_DIR must remain under ${STATE_DIR}" >&2
  exit 13
}

PYTHONPATH="${BRAINK_SOURCE_ROOT}" "${VENV_ROOT}/bin/python" - <<'PY'
from runtime.illlm_ledger import ILLLMImmutableLedger
from runtime.runtime_registry import RuntimeRegistry
from keddeh_saas.braink_bridge import BrainkBridge
print("BRAINK_RUNTIME_IMPORT_PASS")
PY

"${VENV_ROOT}/bin/python" -m compileall -q \
  "${SERVICE_SOURCE}/src" \
  "${BRAINK_SOURCE_ROOT}/runtime/illlm_ledger.py" \
  "${BRAINK_SOURCE_ROOT}/runtime/runtime_registry.py"

systemctl daemon-reload
systemctl enable --now "keddeh-saas-control-plane@${INSTANCE}.service"
sleep 2
systemctl is-active --quiet "keddeh-saas-control-plane@${INSTANCE}.service" || {
  systemctl --no-pager --full status "keddeh-saas-control-plane@${INSTANCE}.service" || true
  echo "ERROR: SaaS service process not active" >&2
  exit 14
}

KEDDEH_SAAS_PORT="${KEDDEH_SAAS_PORT:-8000}" \
  "${VENV_ROOT}/bin/python" "${SERVER_REPO}/deploy/validate_keddeh_saas_control_plane.py" \
  --instance "${INSTANCE}" \
  --base-url "http://127.0.0.1:${KEDDEH_SAAS_PORT}"

echo "KEDDEH_SAAS_PROCESS_ACTIVE instance=${INSTANCE}"
echo "NOTE: local process/readback does not establish public ingress or production promotion."
