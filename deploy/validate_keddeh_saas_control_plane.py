#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def service_active(instance: str) -> bool:
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", f"keddeh-saas-control-plane@{instance}.service"],
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default="alpha-production")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--state-root", default=os.getenv("KEDDEH_STATE_ROOT", "/var/lib/keddeh"))
    args = parser.parse_args()

    result: dict[str, Any] = {
        "schema": "keddeh.saas.server-carrier-qualification/v1",
        "instance": args.instance,
        "base_url": args.base_url,
        "observed_at_ns": time.time_ns(),
        "process_active": service_active(args.instance),
        "local_http_readback": False,
        "braink_evidence_ready": False,
        "qualification_ready": False,
        "public_ingress": "NOT_TESTED",
        "production_promotion": "NOT_CLAIMED",
    }

    try:
        health = fetch_json(args.base_url.rstrip("/") + "/health")
        ready = fetch_json(args.base_url.rstrip("/") + "/ready")
        braink = fetch_json(args.base_url.rstrip("/") + "/v1/braink/status")
        result["health"] = health
        result["ready"] = ready
        result["braink"] = braink
        result["local_http_readback"] = True
        result["braink_evidence_ready"] = braink.get("status") == "PASS"
        result["qualification_ready"] = bool(
            result["process_active"]
            and health.get("local_evidence_chain") is True
            and ready.get("qualification_ready") is True
            and braink.get("status") == "PASS"
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        result["readback_error"] = f"{type(exc).__name__}:{exc}"

    proof_body = dict(result)
    result["proof_root"] = hashlib.sha256(canonical(proof_body)).hexdigest()

    state_dir = Path(args.state_root) / "saas" / args.instance
    state_dir.mkdir(parents=True, exist_ok=True)
    output = state_dir / "qualification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["qualification_ready"] else 20


if __name__ == "__main__":
    raise SystemExit(main())
