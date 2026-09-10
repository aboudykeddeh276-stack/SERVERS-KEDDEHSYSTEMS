#!/usr/bin/env bash
set -euo pipefail

NODE_ID="${1:-alpha-production}"
REPO_SRC="${KEX_REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_ROOT="${KEX_INSTALL_ROOT:-/opt/keddeh/SERVERS-KEDDEHSYSTEMS}"
ENV_FILE="/etc/keddeh/backbone/${NODE_ID}.env"
HOST_RECEIPT="${BRAINK_HOST_ACTIVATION_RECEIPT:-/var/lib/braink/host-activation/activation-receipt.json}"
BACKBONE_RECEIPTS="${INSTALL_ROOT}/runtime/backbone/state/backbone_receipts.jsonl"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 2
fi
command -v python3 >/dev/null || { echo "ERROR: python3 missing" >&2; exit 3; }
[[ -r "${HOST_RECEIPT}" ]] || { echo "ERROR: BRAINK HOST_READY receipt missing: ${HOST_RECEIPT}" >&2; exit 4; }

python3 - "${HOST_RECEIPT}" <<'PY'
import json,sys,time
from pathlib import Path
p=Path(sys.argv[1]); r=json.loads(p.read_text())
if r.get('status')!='HOST_READY' or r.get('admission_state')!='HOST_READY' or r.get('observed_mode')!='ONLINE':
    raise SystemExit('HOST_ACTIVATION_NOT_READY')
activated=int(r.get('activated_ns',0))
age=(time.time_ns()-activated)/1e9 if activated else 1e99
if age < 0 or age > 300:
    raise SystemExit(f'HOST_ACTIVATION_STALE:{age:.3f}')
print(json.dumps({'host_gate':'PASS','host_id':r.get('host_id'),'node_id':r.get('node_id'),'age_sec':round(age,3),'proof_root':r.get('proof_root')}))
PY

"${REPO_SRC}/deploy/install_keddeh_backbone.sh" "${NODE_ID}"
[[ -r "${ENV_FILE}" ]] || { echo "ERROR: backbone env missing after installer" >&2; exit 5; }
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

DNS_HOST="${KEX_DNS_BIND:-127.0.0.1}"
DNS_PORT="${KEX_DNS_PORT:-9053}"
MESH_HOST="${KEX_MESH_BIND:-127.0.0.1}"
MESH_PORT="${KEX_MESH_PORT:-16001}"

python3 - "${INSTALL_ROOT}" "${DNS_HOST}" "${DNS_PORT}" "${MESH_HOST}" "${MESH_PORT}" <<'PY'
import json,socket,struct,sys,time
from pathlib import Path
root=Path(sys.argv[1]); dns_host=sys.argv[2]; dns_port=int(sys.argv[3]); mesh_host=sys.argv[4]; mesh_port=int(sys.argv[5])
da=root/'runtime'/'domain_authority'
sys.path.insert(0,str(da))
from kex_registrar_service import get_zone,get_records
zone=get_zone('keddeh.systems')
if not zone or zone.get('status')!='ACTIVE':
    raise SystemExit('DA_ZONE_NOT_ACTIVE')
records=get_records('alpha.keddeh.systems','A')
if not records:
    raise SystemExit('DA_ALPHA_RECORD_MISSING')

def qname(name):
    return b''.join(bytes([len(x)])+x.encode() for x in name.split('.'))+b'\0'
query=struct.pack('!HHHHHH',0x4b45,0x0100,1,0,0,0)+qname('alpha.keddeh.systems')+struct.pack('!HH',1,1)

u=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); u.settimeout(3); u.sendto(query,(dns_host,dns_port)); data,_=u.recvfrom(4096); u.close()
if len(data)<12: raise SystemExit('DNS_UDP_SHORT_RESPONSE')
txid,flags,qd,an,ns,ar=struct.unpack('!HHHHHH',data[:12])
if txid!=0x4b45 or not (flags & 0x8000) or not (flags & 0x0400) or an<1:
    raise SystemExit('DNS_UDP_NOT_AUTHORITATIVE')

with socket.create_connection((dns_host,dns_port),timeout=3) as s:
    s.sendall(struct.pack('!H',len(query))+query)
    h=s.recv(2)
    if len(h)!=2: raise SystemExit('DNS_TCP_NO_LENGTH')
    n=struct.unpack('!H',h)[0]; buf=b''
    while len(buf)<n:
        p=s.recv(n-len(buf))
        if not p: break
        buf+=p
    if len(buf)<12: raise SystemExit('DNS_TCP_SHORT_RESPONSE')
    txid,flags,qd,an,ns,ar=struct.unpack('!HHHHHH',buf[:12])
    if txid!=0x4b45 or not (flags & 0x8000) or not (flags & 0x0400) or an<1:
        raise SystemExit('DNS_TCP_NOT_AUTHORITATIVE')

with socket.create_connection((mesh_host,mesh_port),timeout=3):
    pass

print(json.dumps({
  'network_probe':'PASS',
  'da_zone':'ACTIVE',
  'dns_udp':'AUTHORITATIVE',
  'dns_tcp':'AUTHORITATIVE',
  'mesh_tcp':'LISTENING',
  'dns_endpoint':f'{dns_host}:{dns_port}',
  'mesh_endpoint':f'{mesh_host}:{mesh_port}',
  'timestamp_ns':time.time_ns()
}))
PY

systemctl is-active --quiet "keddeh-backbone@${NODE_ID}.service" || { echo "ERROR: backbone service not active after probes" >&2; exit 6; }

[[ -r "${BACKBONE_RECEIPTS}" ]] || { echo "ERROR: backbone receipt log missing" >&2; exit 7; }
grep -q '"event":"BACKBONE_READY"' "${BACKBONE_RECEIPTS}" || { echo "ERROR: BACKBONE_READY receipt missing" >&2; exit 8; }
grep -q '"event":"DNS_LISTENING"' "${BACKBONE_RECEIPTS}" || { echo "ERROR: DNS_LISTENING receipt missing" >&2; exit 9; }
grep -q '"event":"MESH_LISTENING"' "${BACKBONE_RECEIPTS}" || { echo "ERROR: MESH_LISTENING receipt missing" >&2; exit 10; }

echo "NETWORK_STACK_PROVEN_LIVE node=${NODE_ID} host_receipt=${HOST_RECEIPT}"
