#!/usr/bin/env bash
set -euo pipefail

NODE_ID="${1:-alpha-production}"
REPO_SRC="${KEX_REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_ROOT="${KEX_INSTALL_ROOT:-/opt/keddeh/SERVERS-KEDDEHSYSTEMS}"
ENV_DIR="/etc/keddeh/backbone"
ENV_FILE="${ENV_DIR}/${NODE_ID}.env"
SERVICE_SRC="${REPO_SRC}/runtime/backbone/systemd/keddeh-backbone@.service"
SERVICE_DST="/etc/systemd/system/keddeh-backbone@.service"
EXAMPLE_ENV="${REPO_SRC}/runtime/backbone/config/node.env.example"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 2
fi

command -v python3 >/dev/null || { echo "ERROR: python3 missing" >&2; exit 3; }
command -v systemctl >/dev/null || { echo "ERROR: systemd missing" >&2; exit 4; }

if ! id keddeh >/dev/null 2>&1; then
  useradd --system --home-dir /opt/keddeh --create-home --shell /usr/sbin/nologin keddeh
fi

mkdir -p "${INSTALL_ROOT}" "${ENV_DIR}" /etc/keddeh/tls
rsync -a --delete --exclude '.git' "${REPO_SRC}/" "${INSTALL_ROOT}/"
mkdir -p "${INSTALL_ROOT}/runtime/backbone/state" "${INSTALL_ROOT}/runtime/domain_authority/substrate_ledger"
chown -R keddeh:keddeh /opt/keddeh

install -m 0644 "${SERVICE_SRC}" "${SERVICE_DST}"

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0600 "${EXAMPLE_ENV}" "${ENV_FILE}"
  sed -i "s/^KEX_NODE_ID=.*/KEX_NODE_ID=${NODE_ID}/" "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Bind KEX_MESH_SECRET, peer addresses, and TLS files before activation." >&2
  echo "SERVICE_NOT_STARTED_CONFIG_REQUIRED"
  systemctl daemon-reload
  exit 10
fi

# Fail closed before starting any exposed service.
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

[[ -n "${KEX_MESH_SECRET:-}" && "${KEX_MESH_SECRET}" != "REPLACE_ON_HOST" ]] || { echo "ERROR: KEX_MESH_SECRET unbound" >&2; exit 11; }

if [[ "${KEX_MESH_BIND:-127.0.0.1}" != "127.0.0.1" && "${KEX_MESH_BIND:-}" != "::1" && "${KEX_MESH_BIND:-}" != "localhost" ]]; then
  [[ -r "${KEX_MESH_TLS_CERT:-}" && -r "${KEX_MESH_TLS_KEY:-}" ]] || { echo "ERROR: non-loopback mesh requires readable TLS cert/key" >&2; exit 12; }
fi

/usr/bin/python3 "${INSTALL_ROOT}/runtime/backbone/keddeh_mesh_backbone.py" --self-test
systemctl daemon-reload
systemctl enable --now "keddeh-backbone@${NODE_ID}.service"
sleep 2
systemctl --no-pager --full status "keddeh-backbone@${NODE_ID}.service" || true
systemctl is-active --quiet "keddeh-backbone@${NODE_ID}.service" || { echo "ERROR: service not active" >&2; exit 13; }

echo "KEDDEH_BACKBONE_ACTIVE node=${NODE_ID}"
