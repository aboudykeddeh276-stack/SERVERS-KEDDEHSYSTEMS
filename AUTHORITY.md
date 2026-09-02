# SERVERS-KEDDEHSYSTEMS Authority Contract

## Sector Class
Infrastructure execution / server runtime.

## Owns
- server process runtimes;
- listener and host binding;
- ingress and transport surfaces;
- authoritative DNS server execution mechanics;
- runtime qualification of bound services;
- server-side persistence mechanics used by resident services.

## Does Not Own
- `.au` parent delegation authority;
- registrar or registry institutional authority;
- public IP allocation authority unless a resident actuator is actually present;
- CasePath or ClaimPath business semantics;
- BRAINK Observer² governance semantics;
- proof by assertion from actuator receipts.

## Current Domain Authority Execution Surface

Resident implementation:

- `runtime/domain_authority/kex_registrar_service.py`
- `runtime/domain_authority/kex_dns.py`
- `runtime/domain_authority/KEX_DA_SERVER_QUALIFICATION_R1.json`
- `runtime/domain_authority/KEX_DA_HOST_BIND_R1.json`

Observed capability includes registrar persistence, persistent zones and records, SOA, NS, A, AAAA, CNAME, MX, TXT, CAA, authoritative NXDOMAIN, UDP DNS, TCP DNS, all-interface bind on port 53, and private-interface readback.

## Current Mechanical Boundary

`PUBLIC_HOST_REQUIRED`

The current carrier has no established publicly routable authoritative DNS host allocation. A bind to `0.0.0.0:53` or reachability on a private RFC1918-style interface does not constitute Internet reachability or parent delegation.

## Mutation Rule

No server action is promoted to externally effective until environmental readback establishes the expected result from the relevant vantage.

## Benchmark Qualification Rule

The Domain Authority runtime must be qualified with repeated runs, concurrency, restart/rehydration, persistence verification, malformed/failure cases, resource measurements, and external comparison against established authoritative-DNS operational expectations. Internal PASS results alone establish only internal test status.

## Cross-Sector Dependencies

- BRAINK: Observer²/orchestrator governance and causal evidence mechanics.
- DOMAIN-AUTHORITY: registrar/delegation/DNSSEC authority contracts.
- NETWORK-FABRIC: routing, NAT, anycast, transport and network exposure.
- CLOUD-INFRASTRUCTURE: public compute/public address allocation when required.
- EVIDENCE-LEDGER: durable qualification and conformance evidence.
