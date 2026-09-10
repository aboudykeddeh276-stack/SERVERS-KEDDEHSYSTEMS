#!/usr/bin/env python3
"""External observer for Keddeh network live-promotion receipts.

Run on a host distinct from the target node. It proves authoritative DNS over
UDP and TCP plus authenticated mesh PING/PONG. It does not configure the target.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import socket
import ssl
import struct
import time
from pathlib import Path
from typing import Any, Dict


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def qname(name: str) -> bytes:
    labels = name.rstrip('.').split('.')
    return b''.join(bytes([len(label.encode())]) + label.encode() for label in labels) + b'\0'


def dns_query(name: str, host: str, port: int, tcp: bool) -> Dict[str, Any]:
    txid = 0x4B45
    query = struct.pack('!HHHHHH', txid, 0x0100, 1, 0, 0, 0) + qname(name) + struct.pack('!HH', 1, 1)
    started = time.monotonic()
    if tcp:
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.settimeout(5)
            sock.sendall(struct.pack('!H', len(query)) + query)
            header = sock.recv(2)
            if len(header) != 2:
                raise RuntimeError('DNS_TCP_NO_LENGTH')
            length = struct.unpack('!H', header)[0]
            data = bytearray()
            while len(data) < length:
                part = sock.recv(length - len(data))
                if not part:
                    raise RuntimeError('DNS_TCP_TRUNCATED')
                data.extend(part)
            response = bytes(data)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(5)
            sock.sendto(query, (host, port))
            response, _ = sock.recvfrom(4096)
        finally:
            sock.close()
    if len(response) < 12:
        raise RuntimeError('DNS_SHORT_RESPONSE')
    rxid, flags, qd, an, ns, ar = struct.unpack('!HHHHHH', response[:12])
    if rxid != txid or not flags & 0x8000 or not flags & 0x0400 or an < 1:
        raise RuntimeError('DNS_NOT_AUTHORITATIVE')
    return {
        'status': 'AUTHORITATIVE',
        'transport': 'TCP' if tcp else 'UDP',
        'answers': an,
        'latency_ms': round((time.monotonic() - started) * 1000, 3),
        'response_root': hashlib.sha256(response).hexdigest(),
    }


def mesh_probe(host: str, port: int, node_id: str, secret: bytes, ca: str, cert: str, key: str) -> Dict[str, Any]:
    if not secret:
        raise RuntimeError('MESH_SECRET_UNBOUND')
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    payload = {'op': 'PING', 'node_id': os.getenv('KEX_OBSERVER_ID', socket.gethostname()), 'timestamp': time.time()}
    envelope = {'payload': payload, 'signature': hmac.new(secret, canon(payload), hashlib.sha256).hexdigest()}
    started = time.monotonic()
    with socket.create_connection((host, port), timeout=5) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as sock:
            sock.settimeout(5)
            sock.sendall(canon(envelope) + b'\n')
            data = bytearray()
            while b'\n' not in data and len(data) < (1 << 20):
                part = sock.recv(65536)
                if not part:
                    break
                data.extend(part)
    if not data:
        raise RuntimeError('MESH_NO_RESPONSE')
    response = json.loads(bytes(data).split(b'\n', 1)[0])
    body = response.get('payload')
    signature = str(response.get('signature', ''))
    if not isinstance(body, dict):
        raise RuntimeError('MESH_BAD_RESPONSE')
    expected = hmac.new(secret, canon(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise RuntimeError('MESH_BAD_SIGNATURE')
    if body.get('op') != 'PONG' or body.get('ok') is not True or body.get('node_id') != node_id:
        raise RuntimeError('MESH_BAD_PONG')
    return {
        'status': 'AUTHENTICATED_PING_PONG',
        'latency_ms': round((time.monotonic() - started) * 1000, 3),
        'response_root': sha(response),
        'tls_peer': host,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target-node-id', required=True)
    parser.add_argument('--dns-host', required=True)
    parser.add_argument('--dns-port', type=int, default=53)
    parser.add_argument('--mesh-host', required=True)
    parser.add_argument('--mesh-port', type=int, default=16001)
    parser.add_argument('--dns-name')
    parser.add_argument('--mesh-secret-file')
    parser.add_argument('--tls-ca', required=True)
    parser.add_argument('--tls-cert', required=True)
    parser.add_argument('--tls-key', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    observer_id = os.getenv('KEX_OBSERVER_ID', socket.gethostname())
    if observer_id == args.target_node_id:
        raise SystemExit('OBSERVER_MUST_BE_DISTINCT_FROM_TARGET')
    secret = (
        Path(args.mesh_secret_file).read_bytes().strip()
        if args.mesh_secret_file
        else os.getenv('KEX_MESH_SECRET', '').encode()
    )
    name = args.dns_name or f'{args.target_node_id}.keddeh.systems'
    udp = dns_query(name, args.dns_host, args.dns_port, tcp=False)
    tcp = dns_query(name, args.dns_host, args.dns_port, tcp=True)
    mesh = mesh_probe(
        args.mesh_host,
        args.mesh_port,
        args.target_node_id,
        secret,
        args.tls_ca,
        args.tls_cert,
        args.tls_key,
    )
    receipt = {
        'schema': 'kex.external-network-observer.v1',
        'observer_id': observer_id,
        'target_node_id': args.target_node_id,
        'observed_ns': time.time_ns(),
        'dns_name': name,
        'dns_udp': udp['status'],
        'dns_tcp': tcp['status'],
        'mesh_protocol': mesh['status'],
        'observations': {'udp': udp, 'tcp': tcp, 'mesh': mesh},
    }
    receipt['proof_root'] = sha(receipt)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + '.tmp')
    temp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temp.replace(output)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
