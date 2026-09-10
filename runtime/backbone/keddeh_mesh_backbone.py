#!/usr/bin/env python3
"""Keddeh Systems mesh backbone runtime.

This process joins the existing Domain Authority registrar and authoritative DNS
runtime to a continuously observed TCP mesh/control plane.  It is deliberately
strict about the difference between a private virtual backbone and a globally
routed ISP edge.

GLOBAL BGP mode is refused unless a public ASN and globally routable prefixes
are explicitly supplied.  RFC1918, TEST-NET and private/documentation ASNs are
never rendered as production announcements.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import signal
import socket
import socketserver
import ssl
import sys
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
DA_DIR = HERE.parent / "domain_authority"
sys.path.insert(0, str(DA_DIR))

from kex_dns import KexDNSServer  # noqa: E402
from kex_registrar_service import (  # noqa: E402
    init_registrar_db,
    register_zone,
    upsert_record,
    resolve_domain,
)

STATE_DIR = Path(os.getenv("KEX_BACKBONE_STATE", str(HERE / "state")))
RECEIPT_LOG = STATE_DIR / "backbone_receipts.jsonl"
NODE_ID = os.getenv("KEX_NODE_ID", "alpha-production")
MESH_BIND = os.getenv("KEX_MESH_BIND", "127.0.0.1")
MESH_PORT = int(os.getenv("KEX_MESH_PORT", "16001"))
DNS_BIND = os.getenv("KEX_DNS_BIND", "127.0.0.1")
DNS_PORT = int(os.getenv("KEX_DNS_PORT", "9053"))
HEARTBEAT_SEC = float(os.getenv("KEX_HEARTBEAT_SEC", "10"))
STALE_SEC = float(os.getenv("KEX_STALE_SEC", "30"))
MESH_SECRET = os.getenv("KEX_MESH_SECRET", "")
TLS_CERT = os.getenv("KEX_MESH_TLS_CERT", "")
TLS_KEY = os.getenv("KEX_MESH_TLS_KEY", "")
TLS_CA = os.getenv("KEX_MESH_TLS_CA", "")
PEERS_RAW = os.getenv("KEX_MESH_PEERS", "")

PRIVATE_ASN_16 = range(64512, 65535)
DOC_ASN_16 = range(64496, 64512)
PRIVATE_ASN_32_MIN = 4200000000
PRIVATE_ASN_32_MAX = 4294967294
DOC_ASN_32 = range(65536, 65552)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(obj: object) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def append_receipt(event: str, **fields: object) -> Dict[str, object]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    record: Dict[str, object] = {"timestamp_utc": utc_now(), "node_id": NODE_ID, "event": event, **fields}
    record["proof_root"] = sha256(record)
    with RECEIPT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(json.dumps(record, separators=(",", ":"), ensure_ascii=False), flush=True)
    return record


def sign_payload(payload: Dict[str, object]) -> str:
    if not MESH_SECRET:
        raise RuntimeError("KEX_MESH_SECRET_UNBOUND")
    return hmac.new(MESH_SECRET.encode(), canonical(payload), hashlib.sha256).hexdigest()


def verify_envelope(envelope: Dict[str, object]) -> Dict[str, object]:
    payload = envelope.get("payload")
    signature = str(envelope.get("signature", ""))
    if not isinstance(payload, dict):
        raise ValueError("BAD_PAYLOAD")
    expected = sign_payload(payload)
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("BAD_SIGNATURE")
    ts = float(payload.get("timestamp", 0))
    if abs(time.time() - ts) > 120:
        raise PermissionError("STALE_ENVELOPE")
    return payload


def parse_peers(raw: str) -> List[Tuple[str, str, int]]:
    peers: List[Tuple[str, str, int]] = []
    for item in filter(None, (x.strip() for x in raw.split(","))):
        node, addr = item.split("@", 1)
        host, port = addr.rsplit(":", 1)
        peers.append((node, host, int(port)))
    return peers


def tls_server_context() -> Optional[ssl.SSLContext]:
    if not TLS_CERT or not TLS_KEY:
        if MESH_BIND not in {"127.0.0.1", "::1", "localhost"}:
            raise RuntimeError("NON_LOOPBACK_MESH_REQUIRES_TLS_CERT_AND_KEY")
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(TLS_CERT, TLS_KEY)
    if TLS_CA:
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_verify_locations(TLS_CA)
    return ctx


def tls_client_context() -> Optional[ssl.SSLContext]:
    if not TLS_CA:
        return None
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=TLS_CA)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    if TLS_CERT and TLS_KEY:
        ctx.load_cert_chain(TLS_CERT, TLS_KEY)
    return ctx


@dataclass
class PeerState:
    node_id: str
    host: str
    port: int
    last_attempt_utc: str = ""
    last_success_utc: str = ""
    latency_ms: float = 0.0
    consecutive_success: int = 0
    consecutive_failure: int = 0
    state: str = "UNOBSERVED"


class ThreadedTCP(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler, tls_ctx=None):
        self.tls_ctx = tls_ctx
        super().__init__(server_address, handler)

    def get_request(self):
        sock, addr = super().get_request()
        if self.tls_ctx:
            sock = self.tls_ctx.wrap_socket(sock, server_side=True)
        return sock, addr


class MeshHandler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline(1 << 20)
        if not raw:
            return
        try:
            envelope = json.loads(raw)
            payload = verify_envelope(envelope)
            op = payload.get("op")
            if op == "PING":
                body = {
                    "ok": True,
                    "node_id": NODE_ID,
                    "op": "PONG",
                    "timestamp": time.time(),
                    "dns": f"{DNS_BIND}:{DNS_PORT}",
                }
            elif op == "RESOLVE":
                name = str(payload.get("name", ""))
                body = {"ok": True, "node_id": NODE_ID, "op": "RESOLVE", "name": name, "value": resolve_domain(name), "timestamp": time.time()}
            else:
                body = {"ok": False, "node_id": NODE_ID, "error": "UNSUPPORTED_OP", "timestamp": time.time()}
            reply = {"payload": body, "signature": sign_payload(body)}
            self.wfile.write(canonical(reply) + b"\n")
            append_receipt("MESH_INBOUND", remote=str(self.client_address), op=str(op), accepted=True)
        except Exception as exc:
            append_receipt("MESH_INBOUND_REJECT", remote=str(self.client_address), error=type(exc).__name__, detail=str(exc)[:160])


class Backbone:
    def __init__(self):
        self.dns: Optional[KexDNSServer] = None
        self.mesh: Optional[ThreadedTCP] = None
        self.mesh_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.peers = {node: PeerState(node, host, port) for node, host, port in parse_peers(PEERS_RAW)}

    def seed_authority(self):
        init_registrar_db()
        serial = int(datetime.now(timezone.utc).strftime("%Y%m%d%H"))
        register_zone("keddeh.systems", "ns1.keddeh.systems", "hostmaster.keddeh.systems", serial, "KEX_BACKBONE")
        upsert_record("keddeh.systems", "ns1.keddeh.systems", "A", "127.0.0.1", ttl=60)
        upsert_record("keddeh.systems", "alpha.keddeh.systems", "A", "127.0.0.1", ttl=60)
        append_receipt("DOMAIN_AUTHORITY_READY", zone="keddeh.systems", serial=serial)

    def start(self):
        if not MESH_SECRET:
            raise RuntimeError("KEX_MESH_SECRET_UNBOUND")
        self.seed_authority()
        self.dns = KexDNSServer(DNS_BIND, DNS_PORT)
        self.dns.start()
        append_receipt("DNS_LISTENING", udp=True, tcp=True, bind=DNS_BIND, port=DNS_PORT)
        self.mesh = ThreadedTCP((MESH_BIND, MESH_PORT), MeshHandler, tls_ctx=tls_server_context())
        self.mesh_thread = threading.Thread(target=self.mesh.serve_forever, daemon=True)
        self.mesh_thread.start()
        append_receipt("MESH_LISTENING", bind=MESH_BIND, port=MESH_PORT, tls=bool(TLS_CERT and TLS_KEY))
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def stop(self):
        self.stop_event.set()
        if self.mesh:
            self.mesh.shutdown(); self.mesh.server_close()
        if self.dns:
            self.dns.stop()
        append_receipt("BACKBONE_STOPPED")

    def _heartbeat_loop(self):
        while not self.stop_event.wait(HEARTBEAT_SEC):
            for peer in self.peers.values():
                self.probe_peer(peer)
            append_receipt("BACKBONE_HEARTBEAT", peers={k: asdict(v) for k, v in self.peers.items()})

    def probe_peer(self, peer: PeerState):
        peer.last_attempt_utc = utc_now()
        payload = {"op": "PING", "node_id": NODE_ID, "timestamp": time.time()}
        envelope = {"payload": payload, "signature": sign_payload(payload)}
        started = time.monotonic()
        try:
            raw_sock = socket.create_connection((peer.host, peer.port), timeout=5)
            sock = raw_sock
            client_ctx = tls_client_context()
            if client_ctx:
                sock = client_ctx.wrap_socket(raw_sock, server_hostname=peer.host)
            with sock:
                sock.sendall(canonical(envelope) + b"\n")
                buf = b""
                while b"\n" not in buf and len(buf) < (1 << 20):
                    part = sock.recv(65536)
                    if not part: break
                    buf += part
            response = json.loads(buf.split(b"\n", 1)[0])
            body = verify_envelope(response)
            if body.get("op") != "PONG" or body.get("ok") is not True:
                raise RuntimeError("BAD_PONG")
            peer.latency_ms = round((time.monotonic() - started) * 1000, 3)
            peer.last_success_utc = utc_now()
            peer.consecutive_success += 1
            peer.consecutive_failure = 0
            peer.state = "UP"
            append_receipt("MESH_OUTBOUND_OK", peer=peer.node_id, latency_ms=peer.latency_ms)
        except Exception as exc:
            peer.consecutive_failure += 1
            peer.consecutive_success = 0
            peer.state = "DOWN" if peer.consecutive_failure >= 3 else "DEGRADED"
            append_receipt("MESH_OUTBOUND_FAIL", peer=peer.node_id, error=type(exc).__name__, detail=str(exc)[:160])


def is_public_asn(asn: int) -> bool:
    if asn <= 0 or asn == 23456 or asn == 65535 or asn == 4294967295:
        return False
    if asn in PRIVATE_ASN_16 or asn in DOC_ASN_16 or asn in DOC_ASN_32:
        return False
    if PRIVATE_ASN_32_MIN <= asn <= PRIVATE_ASN_32_MAX:
        return False
    return True


def is_global_prefix(prefix: str) -> bool:
    net = ipaddress.ip_network(prefix, strict=True)
    return bool(net.is_global)


def render_frr_global(asn: int, router_id: str, prefixes: List[str], peers: List[Tuple[str, int]]) -> str:
    if not is_public_asn(asn):
        raise ValueError("GLOBAL_BGP_REQUIRES_PUBLIC_ASN")
    if not prefixes or any(not is_global_prefix(p) for p in prefixes):
        raise ValueError("GLOBAL_BGP_REQUIRES_GLOBALLY_ROUTABLE_PREFIXES")
    if not peers:
        raise ValueError("GLOBAL_BGP_REQUIRES_UPSTREAM_OR_IXP_PEER")
    lines = ["frr defaults traditional", "hostname keddeh-global-edge", "service integrated-vtysh-config", "!", f"router bgp {asn}", f" bgp router-id {router_id}", " no bgp ebgp-requires-policy"]
    for prefix in prefixes:
        lines.append(f" network {prefix}")
    for host, remote_as in peers:
        lines += [f" neighbor {host} remote-as {remote_as}", f" neighbor {host} description KEDDEH_UPSTREAM"]
    lines += ["!", "address-family ipv4 unicast", " maximum-paths 4", "exit-address-family", "!"]
    return "\n".join(lines) + "\n"


def bgp_from_env() -> str:
    asn = int(os.getenv("KEX_PUBLIC_ASN", "0"))
    router_id = os.getenv("KEX_BGP_ROUTER_ID", "")
    prefixes = [x.strip() for x in os.getenv("KEX_PUBLIC_PREFIXES", "").split(",") if x.strip()]
    peers: List[Tuple[str, int]] = []
    for item in filter(None, (x.strip() for x in os.getenv("KEX_BGP_PEERS", "").split(","))):
        host, remote_as = item.rsplit("@", 1)
        peers.append((host, int(remote_as)))
    if not router_id:
        raise ValueError("KEX_BGP_ROUTER_ID_UNBOUND")
    return render_frr_global(asn, router_id, prefixes, peers)


def self_test() -> int:
    assert not is_public_asn(64512)
    assert not is_global_prefix("192.0.2.0/24")
    assert is_public_asn(13335)
    assert is_global_prefix("1.1.1.0/24")
    init_registrar_db()
    register_zone("test.keddeh.systems", "ns.test.keddeh.systems", "hostmaster.test.keddeh.systems", 1, "SELFTEST")
    upsert_record("test.keddeh.systems", "node.test.keddeh.systems", "A", "127.0.0.1", 60)
    assert resolve_domain("node.test.keddeh.systems") is None  # global_routing is distinct from DNS RR authority
    from kex_registrar_service import get_records
    rows = get_records("node.test.keddeh.systems", "A")
    assert rows and rows[0]["value"] == "127.0.0.1"
    print(json.dumps({"self_test": "PASS", "checks": ["private_asn_gate", "testnet_gate", "registrar_zone_record"]}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--render-global-bgp", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.render_global_bgp:
        print(bgp_from_env(), end="")
        return 0

    backbone = Backbone()
    backbone.start()
    stop = threading.Event()
    def _stop(*_): stop.set()
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    append_receipt("BACKBONE_READY", mesh=f"{MESH_BIND}:{MESH_PORT}", dns=f"{DNS_BIND}:{DNS_PORT}", peers=list(backbone.peers))
    while not stop.wait(1):
        pass
    backbone.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
