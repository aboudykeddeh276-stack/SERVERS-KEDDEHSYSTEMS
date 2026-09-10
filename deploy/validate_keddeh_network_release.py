#!/usr/bin/env python3
"""Resident Keddeh network release validator.

Runs without GitHub Actions. It compiles the critical runtime, executes static
self-tests, launches an isolated loopback backbone, proves UDP/TCP DNS and
signed mesh PING/PONG, verifies receipt chaining, then emits a proof receipt.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import py_compile
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def free_port(sock_type: int) -> int:
    sock = socket.socket(socket.AF_INET, sock_type)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def qname(name: str) -> bytes:
    return b''.join(bytes([len(label)]) + label.encode() for label in name.split('.')) + b'\0'


def verify_dns(host: str, port: int, name: str, tcp: bool) -> Dict[str, Any]:
    txid = 0x4B45
    query = struct.pack('!HHHHHH', txid, 0x0100, 1, 0, 0, 0) + qname(name) + struct.pack('!HH', 1, 1)
    started = time.monotonic()
    if tcp:
        with socket.create_connection((host, port), timeout=3) as sock:
            sock.sendall(struct.pack('!H', len(query)) + query)
            header = sock.recv(2)
            if len(header) != 2:
                raise RuntimeError('DNS_TCP_LENGTH_MISSING')
            length = struct.unpack('!H', header)[0]
            response = bytearray()
            while len(response) < length:
                part = sock.recv(length - len(response))
                if not part:
                    raise RuntimeError('DNS_TCP_TRUNCATED')
                response.extend(part)
            data = bytes(response)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(3)
            sock.sendto(query, (host, port))
            data, _ = sock.recvfrom(4096)
        finally:
            sock.close()
    if len(data) < 12:
        raise RuntimeError('DNS_SHORT_RESPONSE')
    rxid, flags, qd, answers, ns, ar = struct.unpack('!HHHHHH', data[:12])
    if rxid != txid or not flags & 0x8000 or not flags & 0x0400 or answers < 1:
        raise RuntimeError('DNS_NOT_AUTHORITATIVE')
    return {
        'transport': 'TCP' if tcp else 'UDP',
        'status': 'AUTHORITATIVE',
        'answers': answers,
        'latency_ms': round((time.monotonic() - started) * 1000, 3),
        'response_root': hashlib.sha256(data).hexdigest(),
    }


def verify_mesh(host: str, port: int, secret: bytes, expected_node: str) -> Dict[str, Any]:
    payload = {'op': 'PING', 'node_id': 'resident-validator', 'timestamp': time.time()}
    envelope = {'payload': payload, 'signature': hmac.new(secret, canon(payload), hashlib.sha256).hexdigest()}
    started = time.monotonic()
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.settimeout(3)
        sock.sendall(canon(envelope) + b'\n')
        raw = bytearray()
        while b'\n' not in raw and len(raw) < (1 << 20):
            part = sock.recv(65536)
            if not part:
                break
            raw.extend(part)
    if not raw:
        raise RuntimeError('MESH_NO_RESPONSE')
    response = json.loads(bytes(raw).split(b'\n', 1)[0])
    body = response.get('payload')
    if not isinstance(body, dict):
        raise RuntimeError('MESH_BAD_RESPONSE')
    expected_sig = hmac.new(secret, canon(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, str(response.get('signature', ''))):
        raise RuntimeError('MESH_BAD_SIGNATURE')
    if body.get('op') != 'PONG' or body.get('ok') is not True or body.get('node_id') != expected_node:
        raise RuntimeError('MESH_BAD_PONG')
    return {
        'status': 'AUTHENTICATED_PING_PONG',
        'latency_ms': round((time.monotonic() - started) * 1000, 3),
        'response_root': sha(response),
    }


def verify_receipts(path: Path) -> Dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        raise RuntimeError('RECEIPTS_EMPTY')
    previous = '0' * 64
    events = []
    for index, row in enumerate(rows, 1):
        proof = row.pop('proof_root', None)
        if row.get('previous_proof_root') != previous:
            raise RuntimeError(f'RECEIPT_CHAIN_BREAK:{index}')
        expected = hashlib.sha256(canon(row)).hexdigest()
        if not hmac.compare_digest(str(proof), expected):
            raise RuntimeError(f'RECEIPT_HASH_MISMATCH:{index}')
        previous = proof
        events.append(row.get('event'))
    required = {'DOMAIN_AUTHORITY_READY', 'DNS_LISTENING', 'MESH_LISTENING', 'BACKBONE_READY', 'MESH_INBOUND'}
    missing = sorted(required - set(events))
    if missing:
        raise RuntimeError('REQUIRED_RECEIPTS_MISSING:' + ','.join(missing))
    return {'entries': len(rows), 'tip': previous, 'events': sorted(set(events))}


def run() -> Dict[str, Any]:
    critical = [
        ROOT / 'runtime/domain_authority/kex_registrar_service.py',
        ROOT / 'runtime/domain_authority/kex_dns.py',
        ROOT / 'runtime/backbone/keddeh_mesh_backbone.py',
        ROOT / 'runtime/backbone/keddeh_global_edge_qualification.py',
        ROOT / 'deploy/keddeh_external_network_observer.py',
    ]
    for path in critical:
        py_compile.compile(str(path), doraise=True)

    subprocess.run([sys.executable, str(ROOT / 'runtime/backbone/keddeh_mesh_backbone.py'), '--self-test'], cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / 'runtime/backbone/keddeh_global_edge_qualification.py'), '--self-test'], cwd=ROOT, check=True, capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dns_port = free_port(socket.SOCK_STREAM)
        mesh_port = free_port(socket.SOCK_STREAM)
        node_id = 'validation-node'
        secret = b'validation-only-secret'
        env = os.environ.copy()
        env.update({
            'KEX_NODE_ID': node_id,
            'KEX_MESH_BIND': '127.0.0.1',
            'KEX_MESH_PORT': str(mesh_port),
            'KEX_DNS_BIND': '127.0.0.1',
            'KEX_DNS_PORT': str(dns_port),
            'KEX_AUTHORITY_IPV4': '127.0.0.1',
            'KEX_HEARTBEAT_SEC': '1',
            'KEX_STALE_SEC': '3',
            'KEX_MESH_SECRET': secret.decode(),
            'KEX_MESH_PEERS': '',
            'KEX_BACKBONE_STATE': str(tmp_path / 'backbone'),
            'KEX_REGISTRAR_DB': str(tmp_path / 'da' / 'registrar.sqlite'),
        })
        log_path = tmp_path / 'runtime.log'
        with log_path.open('w', encoding='utf-8') as log:
            process = subprocess.Popen(
                [sys.executable, str(ROOT / 'runtime/backbone/keddeh_mesh_backbone.py')],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        try:
            deadline = time.time() + 10
            ready = False
            while time.time() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('BACKBONE_EXITED_EARLY:' + log_path.read_text(encoding='utf-8'))
                try:
                    with socket.create_connection(('127.0.0.1', mesh_port), timeout=0.25):
                        ready = True
                        break
                except OSError:
                    time.sleep(0.1)
            if not ready:
                raise RuntimeError('BACKBONE_START_TIMEOUT')

            name = f'{node_id}.keddeh.systems'
            udp = verify_dns('127.0.0.1', dns_port, name, tcp=False)
            tcp = verify_dns('127.0.0.1', dns_port, name, tcp=True)
            mesh = verify_mesh('127.0.0.1', mesh_port, secret, node_id)
            time.sleep(0.2)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

        receipts = verify_receipts(tmp_path / 'backbone' / 'backbone_receipts.jsonl')

    result = {
        'schema': 'kex.network-release-validation.v1',
        'status': 'PASS',
        'scope': 'ISOLATED_RESIDENT_INTEGRATION_NOT_EXTERNAL_PRODUCTION_PROOF',
        'compile_checks': [str(path.relative_to(ROOT)) for path in critical],
        'dns_udp': udp,
        'dns_tcp': tcp,
        'mesh': mesh,
        'receipts': receipts,
        'validated_ns': time.time_ns(),
    }
    result['proof_root'] = sha(result)
    return result


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        result = {
            'schema': 'kex.network-release-validation.v1',
            'status': 'FAIL',
            'error': type(exc).__name__,
            'detail': str(exc),
            'validated_ns': time.time_ns(),
        }
        result['proof_root'] = sha(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
