#!/usr/bin/env python3
"""Server/network carrier-side verifier for R33 bound accountability envelopes.

This verifier does not decide estate governance and does not acquire BRAINK/KEX
state authority.  It verifies a governance-produced envelope before an existing
server/network carrier action is invoked.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ENVELOPE_SCHEMA = "keddeh.accountability-bound-envelope.r33.v1"
DECISION_SCHEMA = "keddeh.accountability-admission.r33.v1"
CARRIER_SCHEMA = "keddeh.server-carrier.accountability-admission.r33.v1"
ADMITTED_TARGETS = {"SERVER_CARRIER", "NETWORK_CARRIER", "DOMAIN_AUTHORITY_CARRIER"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def root(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def verify(envelope: Mapping[str, Any]) -> dict[str, Any]:
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise ValueError("ACCOUNTABILITY_ENVELOPE_SCHEMA_INVALID")
    supplied = str(envelope.get("envelope_root") or "")
    body = {k: v for k, v in envelope.items() if k != "envelope_root"}
    if not supplied or root(body) != supplied:
        raise ValueError("ACCOUNTABILITY_ENVELOPE_ROOT_INVALID")

    decision = envelope.get("decision_receipt")
    if not isinstance(decision, Mapping) or decision.get("schema") != DECISION_SCHEMA:
        raise ValueError("ACCOUNTABILITY_DECISION_RECEIPT_INVALID")
    decision_root = str(decision.get("receipt_root") or "")
    decision_body = {k: v for k, v in decision.items() if k != "receipt_root"}
    if not decision_root or root(decision_body) != decision_root:
        raise ValueError("ACCOUNTABILITY_DECISION_ROOT_INVALID")
    if decision.get("decision") != "ALLOW":
        raise PermissionError("ACCOUNTABILITY_DECISION_NOT_ALLOW")

    target = str(envelope.get("target_domain") or "")
    if target not in ADMITTED_TARGETS:
        raise PermissionError("ACCOUNTABILITY_TARGET_NOT_SERVER_CARRIER")
    if not envelope.get("mutation_authority") or not envelope.get("current_authority_root"):
        raise PermissionError("ACCOUNTABILITY_AUTHORITY_BINDING_REQUIRED")
    if decision.get("subject") != envelope.get("subject") or decision.get("action") != envelope.get("action"):
        raise ValueError("ACCOUNTABILITY_DECISION_ENVELOPE_IDENTITY_MISMATCH")

    receipt = {
        "schema": CARRIER_SCHEMA,
        "state": "CARRIER_ACTION_ADMITTED",
        "envelope_root": envelope["envelope_root"],
        "decision_receipt_root": decision_root,
        "request_root": envelope.get("request_root"),
        "subject": envelope.get("subject"),
        "action": envelope.get("action"),
        "source_domain": envelope.get("source_domain"),
        "target_domain": target,
        "carrier_authority_mutated": False,
        "braink_authority_acquired": False,
        "execution_claim": "NOT_EXECUTED_BY_GATE",
    }
    return {**receipt, "carrier_receipt_root": root(receipt)}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    result = verify(json.loads(args.envelope.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
