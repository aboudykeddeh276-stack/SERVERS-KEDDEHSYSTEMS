#!/usr/bin/env python3
"""Keddeh Systems public-AS / global-edge qualification gate.

This module validates evidence bindings before any profile may be promoted from a
private virtual backbone to a public autonomous-system edge. It does not request
or allocate Internet resources and cannot substitute for RIR/upstream authority.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import time
from pathlib import Path
from typing import Any, Dict, List

PRIVATE_ASN_16 = range(64512, 65535)
DOC_ASN_16 = range(64496, 64512)
DOC_ASN_32 = range(65536, 65552)
PRIVATE_ASN_32_MIN = 4200000000
PRIVATE_ASN_32_MAX = 4294967294


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value: Any) -> str:
    return hashlib.sha256(canon(value).encode()).hexdigest()


def public_asn(asn: int) -> bool:
    if asn <= 0 or asn in {23456, 65535, 4294967295}:
        return False
    if asn in PRIVATE_ASN_16 or asn in DOC_ASN_16 or asn in DOC_ASN_32:
        return False
    return not (PRIVATE_ASN_32_MIN <= asn <= PRIVATE_ASN_32_MAX)


def global_prefix(prefix: str) -> bool:
    try:
        return bool(ipaddress.ip_network(prefix, strict=True).is_global)
    except ValueError:
        return False


def require(profile: Dict[str, Any], path: str, failures: List[str]) -> Any:
    cur: Any = profile
    for part in path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            failures.append(f"MISSING:{path}")
            return None
        cur = cur[part]
    if cur in (None, "", [], {}):
        failures.append(f"EMPTY:{path}")
    return cur


def evaluate(profile: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[str] = []
    operator = require(profile, "operator", failures)
    resources = require(profile, "resources", failures)
    peers = require(profile, "peers", failures)
    routing = require(profile, "routing_security", failures)
    operations = require(profile, "operations", failures)

    asn = 0
    prefixes: List[Dict[str, Any]] = []
    if isinstance(resources, dict):
        try:
            asn = int(resources.get("asn", 0))
        except (TypeError, ValueError):
            asn = 0
        if not public_asn(asn):
            failures.append("RESOURCE:PUBLIC_ASN_REQUIRED")
        if not resources.get("asn_authority_evidence"):
            failures.append("RESOURCE:ASN_AUTHORITY_EVIDENCE_REQUIRED")
        prefixes = resources.get("prefixes", []) if isinstance(resources.get("prefixes", []), list) else []
        if not prefixes:
            failures.append("RESOURCE:PUBLIC_PREFIX_REQUIRED")
        for entry in prefixes:
            prefix = str(entry.get("prefix", "")) if isinstance(entry, dict) else ""
            if not global_prefix(prefix):
                failures.append(f"RESOURCE:NON_GLOBAL_PREFIX:{prefix}")
                continue
            if not entry.get("authority_evidence"):
                failures.append(f"RESOURCE:PREFIX_AUTHORITY_EVIDENCE:{prefix}")
            if entry.get("roa_state") not in {"VALIDATED", "PUBLISHED_VALID"}:
                failures.append(f"RPKI:ROA_NOT_VALIDATED:{prefix}")

    if not isinstance(peers, list) or not peers:
        failures.append("PEERING:UPSTREAM_OR_IXP_REQUIRED")
    else:
        for index, peer in enumerate(peers):
            label = f"peer[{index}]"
            if not isinstance(peer, dict):
                failures.append(f"PEERING:BAD_PROFILE:{label}")
                continue
            if not peer.get("neighbor"):
                failures.append(f"PEERING:NEIGHBOR_REQUIRED:{label}")
            try:
                remote_as = int(peer.get("remote_as", 0))
            except (TypeError, ValueError):
                remote_as = 0
            if not public_asn(remote_as):
                failures.append(f"PEERING:PUBLIC_REMOTE_AS_REQUIRED:{label}")
            if peer.get("relationship") not in {"TRANSIT", "PEER", "IXP_RS", "CUSTOMER"}:
                failures.append(f"PEERING:RELATIONSHIP_REQUIRED:{label}")
            if not peer.get("import_policy_ref"):
                failures.append(f"BGP:IMPORT_POLICY_REQUIRED:{label}")
            if not peer.get("export_policy_ref"):
                failures.append(f"BGP:EXPORT_POLICY_REQUIRED:{label}")
            try:
                max_prefix = int(peer.get("max_prefix", 0))
            except (TypeError, ValueError):
                max_prefix = 0
            if max_prefix <= 0:
                failures.append(f"BGP:MAX_PREFIX_REQUIRED:{label}")

    if isinstance(routing, dict):
        validators = routing.get("rpki_validators", [])
        if not isinstance(validators, list) or len(validators) < 2:
            failures.append("RPKI:REDUNDANT_VALIDATORS_REQUIRED")
        if routing.get("rov_mode") not in {"MONITOR", "REJECT_INVALID"}:
            failures.append("RPKI:ROV_MODE_REQUIRED")
        for flag in ("bogon_filtering", "own_prefix_ingress_filtering", "source_address_validation"):
            if routing.get(flag) is not True:
                failures.append(f"ROUTING_SECURITY:{flag}")
        if not routing.get("session_protection_policy"):
            failures.append("BGP:SESSION_PROTECTION_POLICY_REQUIRED")
        if routing.get("ebgp_default_reject_without_policy") is not True:
            failures.append("BGP:RFC8212_DEFAULT_REJECT_REQUIRED")

    if isinstance(operations, dict):
        for field in (
            "noc_contact",
            "abuse_contact",
            "security_contact",
            "monitoring_ref",
            "rollback_ref",
            "out_of_band_recovery_ref",
            "change_control_ref",
        ):
            if not operations.get(field):
                failures.append(f"OPERATIONS:{field}")

    if not isinstance(operator, dict) or not operator.get("authority_root"):
        failures.append("OPERATOR:AUTHORITY_ROOT_REQUIRED")

    result = {
        "schema": "kex.global-edge-qualification.v1",
        "state": "GLOBAL_EDGE_READY" if not failures else "PUBLIC_AS_HOLD",
        "failures": sorted(set(failures)),
        "asn": asn or None,
        "prefixes": [entry.get("prefix") for entry in prefixes if isinstance(entry, dict)],
        "peer_count": len(peers) if isinstance(peers, list) else 0,
        "evaluated_ns": time.time_ns(),
    }
    result["proof_root"] = sha(result)
    return result


def self_test() -> Dict[str, Any]:
    profile = {
        "operator": {"name": "TEST", "authority_root": "proof:test"},
        "resources": {
            "asn": 13335,
            "asn_authority_evidence": "evidence:test",
            "prefixes": [{"prefix": "1.1.1.0/24", "authority_evidence": "evidence:test", "roa_state": "VALIDATED"}],
        },
        "peers": [{
            "neighbor": "8.8.8.8",
            "remote_as": 15169,
            "relationship": "TRANSIT",
            "import_policy_ref": "policy:in",
            "export_policy_ref": "policy:out",
            "max_prefix": 100,
        }],
        "routing_security": {
            "rpki_validators": ["validator:a", "validator:b"],
            "rov_mode": "MONITOR",
            "bogon_filtering": True,
            "own_prefix_ingress_filtering": True,
            "source_address_validation": True,
            "session_protection_policy": "policy:session",
            "ebgp_default_reject_without_policy": True,
        },
        "operations": {
            "noc_contact": "ops:test",
            "abuse_contact": "abuse:test",
            "security_contact": "security:test",
            "monitoring_ref": "monitor:test",
            "rollback_ref": "rollback:test",
            "out_of_band_recovery_ref": "oob:test",
            "change_control_ref": "change:test",
        },
    }
    ready = evaluate(profile)
    assert ready["state"] == "GLOBAL_EDGE_READY"
    profile["resources"]["asn"] = 64512
    held = evaluate(profile)
    assert held["state"] == "PUBLIC_AS_HOLD"
    assert "RESOURCE:PUBLIC_ASN_REQUIRED" in held["failures"]
    return {"status": "PASS", "checks": ["public_resource_gate", "peer_policy_gate", "rpki_gate", "anti_spoofing_gate", "operations_gate", "fail_closed"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    if args.profile:
        result = evaluate(json.loads(args.profile.read_text(encoding="utf-8")))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["state"] == "GLOBAL_EDGE_READY" else 3
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
