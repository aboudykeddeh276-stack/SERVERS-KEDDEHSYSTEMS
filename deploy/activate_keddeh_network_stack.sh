#!/usr/bin/env bash
set -euo pipefail

NODE_ID="${1:-alpha-production}"
REPO_SRC="${KEX_REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_ROOT="${KEX_INSTALL_ROOT:-/opt/keddeh/SERVERS-KEDDEHSYSTEMS}"
ENV_FILE="/etc/keddeh/backbone/${NODE_ID}.env"
EXTERNAL_RECEIPT="${KEX_EXTERNAL_OBSERVER_RECEIPT:-}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 2
fi
command -v python3 >/dev/null || { echo "ERROR: python3 missing" >&2; exit 3; }
command -v systemctl >/dev/null || { echo "ERROR: systemctl missing" >&2; exit 4; }

# The server/network carrier proves its own host boundary.  No externally
# synthesized host-control component is permitted to grant this state.
"${REPO_SRC}/deploy/install_keddeh_backbone.sh" "${NODE_ID}"
[[ -r "${ENV_FILE}" ]] || { echo "ERROR: backbone env missing after installer" >&2; exit 5; }
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

SERVICE="keddeh-backbone@${NODE_ID}.service"
systemctl is-active --quiet "${SERVICE}" || { echo "ERROR: backbone service not active" >&2; exit 6; }
MAIN_PID="$(systemctl show --property MainPID --value "${SERVICE}")"
[[ "${MAIN_PID}" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: backbone MainPID invalid: ${MAIN_PID}" >&2; exit 7; }
[[ -d "/proc/${MAIN_PID}" ]] || { echo "ERROR: backbone process missing: ${MAIN_PID}" >&2; exit 8; }
[[ -e "/proc/${MAIN_PID}/ns/net" ]] || { echo "ERROR: backbone network namespace unavailable: ${MAIN_PID}" >&2; exit 9; }
NETNS="$(readlink "/proc/${MAIN_PID}/ns/net" || true)"
printf '{"boundary":"HOST_PROCESS_NETWORK_NAMESPACE","state":"OBSERVED","node_id":"%s","pid":%s,"netns":"%s"}\n' "${NODE_ID}" "${MAIN_PID}" "${NETNS}"

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
  'boundary':'HOST_PROTOCOL_STACK',
  'state':'OBSERVED',
  'da_database':'INTEGRITY_OK',
  'da_zone':'ACTIVE_LOCAL_AUTHORITY',
  'dns_name':name,
  'dns_udp':'AUTHORITATIVE_RESPONSE_OBSERVED',
  'dns_tcp':'AUTHORITATIVE_RESPONSE_OBSERVED',
  'mesh_protocol':'AUTHENTICATED_PING_PONG_OBSERVED',
  'public_dns_delegation':'NOT_CLAIMED',
  'public_routing':'NOT_CLAIMED',
  'timestamp_ns':time.time_ns()
}))
PY

[[ -r "${BACKBONE_RECEIPTS}" ]] || { echo "ERROR: backbone receipt log missing: ${BACKBONE_RECEIPTS}" >&2; exit 10; }

python3 - "${BACKBONE_RECEIPTS}" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); lines=[x for x in p.read_text().splitlines() if x.strip()]
if not lines: raise SystemExit('BACKBONE_RECEIPTS_EMPTY')
prev='0'*64; events=[]
for idx,line in enumerate(lines,1):
    stored=json.loads(line); proof=stored.get('proof_root')
    body={k:v for k,v in stored.items() if k!='proof_root'}
    if body.get('previous_proof_root')!=prev:
        raise SystemExit(f'BACKBONE_RECEIPT_CHAIN_BREAK:{idx}')
    expected=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if proof!=expected:
        raise SystemExit(f'BACKBONE_RECEIPT_HASH_MISMATCH:{idx}')
    prev=proof; events.append(body.get('event'))
for event in ('DOMAIN_AUTHORITY_READY','DNS_LISTENING','MESH_LISTENING','BACKBONE_READY','MESH_INBOUND'):
    if event not in events: raise SystemExit(f'BACKBONE_REQUIRED_RECEIPT_MISSING:{event}')
print(json.dumps({'boundary':'BACKBONE_RECEIPT_CHAIN','state':'VERIFIED','entries':len(lines),'tip':prev}))
PY

echo "HOST_PROTOCOL_STACK_OBSERVED node=${NODE_ID} pid=${MAIN_PID}"

if [[ -z "${EXTERNAL_RECEIPT}" ]]; then
  echo "EXTERNAL_PROTOCOL_READBACK_PENDING node=${NODE_ID}"
  exit 20
fi
[[ -r "${EXTERNAL_RECEIPT}" ]] || { echo "ERROR: external observer receipt unreadable: ${EXTERNAL_RECEIPT}" >&2; exit 21; }

python3 - "${EXTERNAL_RECEIPT}" "${NODE_ID}" <<'PY'
import hashlib,json,sys,time
from pathlib import Path
stored=json.loads(Path(sys.argv[1]).read_text()); expected_node=sys.argv[2]
required={'schema','observer_id','target_node_id','observed_ns','dns_udp','dns_tcp','mesh_protocol','proof_root'}
missing=sorted(required-set(stored))
if missing: raise SystemExit('EXTERNAL_RECEIPT_MISSING:'+','.join(missing))
if stored.get('schema')!='kex.external-network-observer.v1': raise SystemExit('EXTERNAL_RECEIPT_SCHEMA_INVALID')
proof=stored.get('proof_root'); body={k:v for k,v in stored.items() if k!='proof_root'}
expected=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
if proof!=expected: raise SystemExit('EXTERNAL_RECEIPT_HASH_INVALID')
if stored['target_node_id']!=expected_node: raise SystemExit('EXTERNAL_RECEIPT_TARGET_MISMATCH')
if stored['observer_id'] in {expected_node,'localhost','127.0.0.1'}: raise SystemExit('EXTERNAL_OBSERVER_ID_NOT_DISTINCT')
age=(time.time_ns()-int(stored['observed_ns']))/1e9
if age<0 or age>300: raise SystemExit(f'EXTERNAL_RECEIPT_STALE:{age:.3f}')
if stored['dns_udp']!='AUTHORITATIVE' or stored['dns_tcp']!='AUTHORITATIVE' or stored['mesh_protocol']!='AUTHENTICATED_PING_PONG':
    raise SystemExit('EXTERNAL_PROTOCOL_READBACK_NOT_VERIFIED')
print(json.dumps({
    'boundary':'EXTERNAL_PROTOCOL_OBSERVATION_RECEIPT',
    'state':'RECEIPT_INTEGRITY_AND_READBACK_VERIFIED',
    'observer_id':stored['observer_id'],
    'age_sec':round(age,3),
    'proof_root':proof,
    'observer_host_independence':'ASSERTED_BY_OBSERVER_ID_NOT_CRYPTOGRAPHICALLY_ATTESTED',
    'public_internet_path':'NOT_CLAIMED',
    'dns_parent_delegation':'NOT_CLAIMED',
    'inter_as_bgp':'NOT_CLAIMED'
}))
PY

echo "EXTERNAL_PROTOCOL_READBACK_RECEIPT_VERIFIED node=${NODE_ID} receipt=${EXTERNAL_RECEIPT}"
