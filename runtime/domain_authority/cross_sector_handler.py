from __future__ import annotations
from typing import Dict, Any
import hashlib, json, time

from . import kex_registrar_service as registrar


def _canon(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _root(v: Any) -> str:
    return hashlib.sha256(_canon(v).encode()).hexdigest()


def execute(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Consume the canonical Keddeh work envelope and apply DOMAIN_AUTHORITY-owned state.

    This handler owns registrar/zone state only. It does not claim server-host, network, parent-delegation,
    TLS, web-publication or evidence-ledger mutations.
    """
    if envelope.get("organisation_identity") != "organisation://the-layna-company":
        raise ValueError("legal identity mismatch")
    if envelope.get("operating_identity") != "business-name://keddeh-systems":
        raise ValueError("operating identity mismatch")

    state = envelope.get("state") or {}
    domain = (state.get("domain") or "").rstrip(".")
    if not domain:
        raise ValueError("domain required")

    registrar.init_registrar_db()
    owner = hashlib.sha256(envelope["operating_identity"].encode()).hexdigest()
    ip = state.get("ip") or "127.0.0.1"
    port = int(state.get("port") or 8081)
    primary_ns = (state.get("primary_ns") or f"ns1.{domain}").rstrip(".")
    secondary_ns = (state.get("secondary_ns") or f"ns2.{domain}").rstrip(".")
    admin_rname = (state.get("admin_rname") or f"hostmaster.{domain}").rstrip(".")
    serial = int(state.get("serial") or int(time.strftime("%Y%m%d01")))

    registrar.register_domain(domain, ip, port, owner)
    registrar.register_zone(domain, primary_ns, admin_rname, serial, owner)
    registrar.upsert_record(domain, domain, "NS", primary_ns, 300)
    registrar.upsert_record(domain, domain, "NS", secondary_ns, 300)
    registrar.upsert_record(domain, domain, "A", ip, 300)

    readback = {
        "domain": domain,
        "route_ip": registrar.resolve_domain(domain),
        "zone": registrar.get_zone(domain),
        "ns": registrar.get_records(domain, "NS"),
        "a": registrar.get_records(domain, "A"),
    }
    result = {
        "sector": "DOMAIN_AUTHORITY",
        "mutation": "REGISTER_DOMAIN_AND_AUTHORITATIVE_ZONE",
        "readback": readback,
        "next_sector": "SERVERS",
        "next_requirement": "bind authoritative DNS server process to the zone and return wire-level readback",
    }
    result["result_root"] = _root(result)
    return result
