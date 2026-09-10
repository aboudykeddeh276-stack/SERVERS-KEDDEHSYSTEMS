#!/usr/bin/env bash
set -euo pipefail

NODE_ID="${1:-alpha-production}"
REPO_SRC="${KEX_REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_ROOT="${KEX_INSTALL_ROOT:-/opt/keddeh/SERVERS-KEDDEHSYSTEMS}"
STATE_ROOT="${KEX_STATE_ROOT:-/var/lib/keddeh}"
ENV_DIR="/etc/keddeh/backbone"
ENV_FILE="${ENV_DIR}/${NODE_ID}.env"
SERVICE_SRC="${REPO_SRC}/runtime/backbone/systemd/keddeh-backbone@.service"
SERVICE_DST="/etc/systemd/system/keddeh-backbone@.service"
EXAMPLE_ENV="${REPO_SRC}/runtime/backbone/config/node.env.example"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 2
fi

for cmd in python3 systemctl rsync; do
  command -v "${cmd}" >/dev/null || { echo "ERROR: ${cmd} missing" >&2; exit 3; }
done

if ! id keddeh >/dev/null 2>&1; then
  useradd --system --home-dir /opt/keddeh --create-home --shell /usr/sbin/nologin keddeh
fi

mkdir -p "${INSTALL_ROOT}" "${ENV_DIR}" /etc/keddeh/tls \
  "${STATE_ROOT}/backbone/${NODE_ID}" "${STATE_ROOT}/domain-authority"

# Code deployment and authority state are deliberately separate. Never rsync-delete /var/lib/keddeh.
rsync -a --delete --exclude '.git' "${REPO_SRC}/" "${INSTALL_ROOT}/"
chown -R root:root "${INSTALL_ROOT}"
chown -R keddeh:keddeh "${STATE_ROOT}/backbone" "${STATE_ROOT}/domain-authority"
chmod 0750 "${STATE_ROOT}" "${STATE_ROOT}/backbone" "${STATE_ROOT}/backbone/${NODE_ID}" "${STATE_ROOT}/domain-authority"

install -m 0644 "${SERVICE_SRC}" "${SERVICE_DST}"

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0600 "${EXAMPLE_ENV}" "${ENV_FILE}"
  sed -i "s/^KEX_NODE_ID=.*/KEX_NODE_ID=${NODE_ID}/" "${ENV_FILE}"
  sed -i "s#^KEX_BACKBONE_STATE=.*#KEX_BACKBONE_STATE=${STATE_ROOT}/backbone/${NODE_ID}#" "${ENV_FILE}"
  sed -i "s#^KEX_REGISTRAR_DB=.*#KEX_REGISTRAR_DB=${STATE_ROOT}/domain-authority/keddeh_registrar.sqlite#" "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Bind node addresses, KEX_MESH_SECRET, peers and mTLS files before activation." >&2
  echo "SERVICE_NOT_STARTED_CONFIG_REQUIRED"
  systemctl daemon-reload
  exit 10
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

[[ -n "${KEX_MESH_SECRET:-}" && "${KEX_MESH_SECRET}" != "REPLACE_ON_HOST" ]] || {
  echo "ERROR: KEX_MESH_SECRET unbound" >&2; exit 11;
}

NON_LOOPBACK=false
case "${KEX_MESH_BIND:-127.0.0.1}" in
  127.0.0.1|::1|localhost) ;;
  *) NON_LOOPBACK=true ;;
esac

if [[ "${NON_LOOPBACK}" == true ]]; then
  [[ -r "${KEX_MESH_TLS_CERT:-}" && -r "${KEX_MESH_TLS_KEY:-}" && -r "${KEX_MESH_TLS_CA:-}" ]] || {
    echo "ERROR: non-loopback mesh requires readable TLS cert, key and CA" >&2; exit 12;
  }
fi

if [[ "${KEX_DNS_BIND:-127.0.0.1}" != "127.0.0.1" && "${KEX_DNS_BIND:-}" != "::1" && "${KEX_DNS_BIND:-}" != "localhost" ]]; then
  [[ -n "${KEX_AUTHORITY_IPV4:-}" && "${KEX_AUTHORITY_IPV4}" != "REPLACE_ON_HOST" ]] || {
    echo "ERROR: exposed DNS requires KEX_AUTHORITY_IPV4 for authoritative publication" >&2; exit 13;
  }
fi

/usr/bin/python3 "${INSTALL_ROOT}/runtime/domain_authority/kex_registrar_service.py" >/dev/null
/usr/bin/python3 "${INSTALL_ROOT}/runtime/backbone/keddeh_mesh_backbone.py" --self-test

systemctl daemon-reload
systemctl enable --now "keddeh-backbone@${NODE_ID}.service"
sleep 2
systemctl is-active --quiet "keddeh-backbone@${NODE_ID}.service" || {
  systemctl --no-pager --full status "keddeh-backbone@${NODE_ID}.service" || true
  echo "ERROR: service not active" >&2
  exit 14
}

echo "KEDDEH_BACKBONE_PROCESS_ACTIVE node=${NODE_ID}"
echo "NOTE: process-active is not PROVEN_LIVE; run deploy/activate_keddeh_network_stack.sh for socket/readback proof."
