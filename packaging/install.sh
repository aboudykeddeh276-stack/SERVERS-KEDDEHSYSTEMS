#!/usr/bin/env bash
set -euo pipefail
SOURCE_ROOT="$(pwd)"
INSTALL_ROOT="/opt/keddeh/SERVERS-KEDDEHSYSTEMS"
ENABLE_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE_ROOT="$(cd "$2" && pwd)"; shift 2 ;;
    --install-root) INSTALL_ROOT="$2"; shift 2 ;;
    --enable-only) ENABLE_ONLY=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ "${EUID}" -eq 0 ]] || { echo "run as root" >&2; exit 2; }
for cmd in python3 install rsync systemctl systemd-analyze; do command -v "$cmd" >/dev/null || { echo "missing: $cmd" >&2; exit 3; }; done
python3 "${SOURCE_ROOT}/packaging/bin/keddeh-index.py" --root "${SOURCE_ROOT}"
systemd-sysusers "${SOURCE_ROOT}/packaging/systemd/keddeh.sysusers"
systemd-tmpfiles --create "${SOURCE_ROOT}/packaging/systemd/keddeh.tmpfiles"
if [[ "$ENABLE_ONLY" -eq 0 ]]; then
  install -d -m 0755 "${INSTALL_ROOT}"
  rsync -a --delete --exclude .git "${SOURCE_ROOT}/" "${INSTALL_ROOT}/"
  chown -R root:root "${INSTALL_ROOT}"
  find "${INSTALL_ROOT}" -type d -exec chmod 0755 {} +
fi
install -d -m 0755 /etc/keddeh/modules /etc/systemd/system
install -m 0644 "${INSTALL_ROOT}/packaging/runtime.index.json" /etc/keddeh/runtime.index.json
for idx in "${INSTALL_ROOT}"/packaging/modules/*/module.index.json; do
  id="$(basename "$(dirname "$idx")")"
  install -d -m 0755 "/etc/keddeh/modules/${id}"
  install -m 0644 "$idx" "/etc/keddeh/modules/${id}/module.index.json"
done
install -m 0644 "${INSTALL_ROOT}"/packaging/systemd/*.service /etc/systemd/system/
install -m 0644 "${INSTALL_ROOT}"/packaging/systemd/*.target /etc/systemd/system/
install -m 0644 "${INSTALL_ROOT}"/packaging/systemd/*.timer /etc/systemd/system/
install -m 0644 "${INSTALL_ROOT}"/packaging/systemd/*.path /etc/systemd/system/
systemd-analyze verify "${INSTALL_ROOT}"/packaging/systemd/*.service "${INSTALL_ROOT}"/packaging/systemd/*.target "${INSTALL_ROOT}"/packaging/systemd/*.timer "${INSTALL_ROOT}"/packaging/systemd/*.path
systemctl daemon-reload
systemctl enable keddeh-runtime.target keddeh-module-reconcile.timer keddeh-module-index.path
echo "KEDDEH_PACKAGING_INSTALLED activation=explicit code=${INSTALL_ROOT}"
