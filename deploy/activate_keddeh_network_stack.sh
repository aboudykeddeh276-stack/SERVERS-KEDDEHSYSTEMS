#!/usr/bin/env bash
set -euo pipefail

NODE_ID="${1:-alpha-production}"
REPO_SRC="${KEX_REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_ROOT="${KEX_INSTALL_ROOT:-/opt/keddeh/SERVERS-KEDDEHSYSTEMS}"
ENV_FILE="/etc/keddeh/backbone/${NODE_ID}.env"
HOST_RECEIPT="${BRAINK_HOST_ACTIVATION_RECEIPT:-/var/lib/braink/host-activation/activation-receipt.json}"
EXTERNAL_RECEIPT="${KEX_EXTERNAL_OBSERVER_RECEIPT:-}"

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

BACKBONE_STATE="${KEX_BACKBONE_STATE:-/var/lib/keddeh/backbone/${NODE_ID}}"
BACKBONE_RECEIPTS="${BACKBONE_STATE}/backbone_receipts.jsonl"
DNS_PORT="${KEX_DNS_PORT:-9053}"
MESH_PORT="${KEX_MESH_PORT:-16001}"
DNS_PROBE_HOST="${KEX_DNS_PROBE_HOST:-127.0.0.1}"
MESH_PROBE_HOST="${KEX_MESH_PROBE_HOST:-127.0.0.1}"

python3 - "${INSTALL_ROOT}" "${NODE_ID}" "${DNS_PROBE_HOST}" "${DNS_PORT}" "${MESH_PROBE_HOST}" "${MESH_PORT}" "${KEX_MESH_SECRET}" <<'PY'
import hashlib,hmac,json,socket,struct,sys,time
from pathlib import Path

root=Path(sys.argv[1]); node_id=sys.argv[2]
dns_host=sys.argv[3]; dns_port=int(sys.argv[4])
mesh_host=sys.argv[5]; mesh_port=int(sys.argv[6]); secret=sys.argv[7].encode()
da=root/'runtime'/'domain_authority'; sys.path.insert(0,str(da))
from kex_registrar_service import database_health,get_zone,get_records

health=database_health()
if health.get('integrity')!='ok':
    raise SystemExit('DA_DATABASE_INTEGRITY_FAILED')
zone=get_zone('keddeh.systems')
if not zone or zone.get('status')!='ACTIVE':
    raise SystemExit('DA_ZONE_NOT_ACTIVE')
name=f'{node_id}.keddeh.systems'
records=get_records(name,'A')
if not records:
    raise SystemExit(f'DA_NODE_RECORD_MISSING:{name}')

def qname(n):
    return b''.join(bytes([len(x)])+x.encode() for x in n.split('.'))+b'\0'
query=struct.pack('!HHHHHH',0x4b45,0x0100,1,0,0,0)+qname(name)+struct.pack('!HH',1,1)

u=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); u.settimeout(3)
u.sendto(query,(dns_host,dns_port)); data,_=u.recvfrom(4096); u.close()
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
        part=s.recv(n-len(buf))
        if not part: break
        buf+=part
    if len(buf)<12: raise SystemExit('DNS_TCP_SHORT_RESPONSE')
    txid,flags,qd,an,ns,ar=struct.unpack('!HHHHHH',buf[:12])
    if txid!=0x4b45 or not (flags & 0x8000) or not (flags & 0x0400) or an<1:
        raise SystemExit('DNS_TCP_NOT_AUTHORITATIVE')

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sign(payload):
    return hmac.new(secret,canonical(payload),hashlib.sha256).hexdigest()
payload={'op':'PING','node_id':'activation-probe','timestamp':time.time()}
envelope={'payload':payload,'signature':sign(payload)}
with socket.create_connection((mesh_host,mesh_port),timeout=3) as s:
    s.settimeout(3); s.sendall(canonical(envelope)+b'\n'); raw=b''
    while b'\n' not in raw and len(raw)<1048576:
        part=s.recv(65536)
        if not part: break
        raw+=part
if not raw: raise SystemExit('MESH_NO_RESPONSE')
response=json.loads(raw.split(b'\n',1)[0]); body=response.get('payload')
if not isinstance(body,dict) or not hmac.compare_digest(sign(body),str(response.get('signature',''))):
    raise SystemExit('MESH_RESPONSE_SIGNATURE_INVALID')
if body.get('op')!='PONG' or body.get('ok') is not True or body.get('node_id')!=node_id:
    raise SystemExit('MESH_AUTHENTICATED_PONG_INVALID')

print(json.dumps({
  'host_network_probe':'PASS',
  'da_database':'INTEGRITY_OK',
  'da_zone':'ACTIVE',
  'dns_name':name,
  'dns_udp':'AUTHORITATIVE',
  'dns_tcp':'AUTHORITATIVE',
  'mesh_protocol':'AUTHENTICATED_PING_PONG',
  'timestamp_ns':time.time_ns()
}))
PY

systemctl is-active --quiet "keddeh-backbone@${NODE_ID}.service" || { echo "ERROR: backbone service not active after probes" >&2; exit 6; }
[[ -r "${BACKBONE_RECEIPTS}" ]] || { echo "ERROR: backbone receipt log missing: ${BACKBONE_RECEIPTS}" >&2; exit 7; }

python3 - "${BACKBONE_RECEIPTS}" <<'PY'
import hashlib,json,sys,time
from pathlib import Path
p=Path(sys.argv[1]); lines=[x for x in p.read_text().splitlines() if x.strip()]
if not lines: raise SystemExit('BACKBONE_RECEIPTS_EMPTY')
prev='0'*64; events=[]
for idx,line in enumerate(lines,1):
    r=json.loads(line); proof=r.pop('proof_root',None)
    if r.get('previous_proof_root')!=prev:
        raise SystemExit(f'BACKBONE_RECEIPT_CHAIN_BREAK:{idx}')
    expected=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if proof!=expected:
        raise SystemExit(f'BACKBONE_RECEIPT_HASH_MISMATCH:{idx}')
    prev=proof; events.append(r.get('event'))
for event in ('DOMAIN_AUTHORITY_READY','DNS_LISTENING','MESH_LISTENING','BACKBONE_READY','MESH_INBOUND'):
    if event not in events: raise SystemExit(f'BACKBONE_REQUIRED_RECEIPT_MISSING:{event}')
print(json.dumps({'receipt_chain':'PASS','entries':len(lines),'tip':prev}))
PY

echo "HOST_NETWORK_PROVEN node=${NODE_ID} host_receipt=${HOST_RECEIPT}"

if [[ -z "${EXTERNAL_RECEIPT}" ]]; then
  echo "NETWORK_STACK_EXTERNAL_PROOF_PENDING node=${NODE_ID}"
  exit 20
fi
[[ -r "${EXTERNAL_RECEIPT}" ]] || { echo "ERROR: external observer receipt unreadable: ${EXTERNAL_RECEIPT}" >&2; exit 21; }

python3 - "${EXTERNAL_RECEIPT}" "${NODE_ID}" <<'PY'
import json,sys,time
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); expected_node=sys.argv[2]
required={'observer_id','target_node_id','observed_ns','dns_udp','dns_tcp','mesh_protocol','proof_root'}
missing=sorted(required-set(r))
if missing: raise SystemExit('EXTERNAL_RECEIPT_MISSING:'+','.join(missing))
if r['target_node_id']!=expected_node: raise SystemExit('EXTERNAL_RECEIPT_TARGET_MISMATCH')
if r['observer_id'] in {expected_node,'localhost','127.0.0.1'}: raise SystemExit('EXTERNAL_OBSERVER_NOT_DISTINCT')
age=(time.time_ns()-int(r['observed_ns']))/1e9
if age<0 or age>300: raise SystemExit(f'EXTERNAL_RECEIPT_STALE:{age:.3f}')
if r['dns_udp']!='AUTHORITATIVE' or r['dns_tcp']!='AUTHORITATIVE' or r['mesh_protocol']!='AUTHENTICATED_PING_PONG':
    raise SystemExit('EXTERNAL_NETWORK_PROBE_NOT_PROVEN')
print(json.dumps({'external_observer_gate':'PASS','observer_id':r['observer_id'],'age_sec':round(age,3),'proof_root':r['proof_root']}))
PY

echo "NETWORK_STACK_PROVEN_LIVE node=${NODE_ID} external_observer=${EXTERNAL_RECEIPT}"
