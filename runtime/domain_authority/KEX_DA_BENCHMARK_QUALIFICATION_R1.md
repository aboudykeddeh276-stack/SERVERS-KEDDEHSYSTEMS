# KEX Domain Authority Benchmark Qualification R1

## Tested Implementation Scope

This qualification contract applies to the resident registrar/DNS path:

- `kex_registrar_service.py`
- `kex_dns.py`

The exact implementation commit SHAs used by every benchmark run must be captured in the resulting receipt.

## Benchmark Groups

### B01 Repeated Run
Execute identical registrar and DNS workloads repeatedly from a clean and a warmed state. Record count, success/failure, latency distribution, state digests and output consistency.

### B02 UDP Concurrency
Exercise authoritative UDP queries concurrently across existing RR types and NXDOMAIN. Record requested concurrency, completed queries, errors, throughput, p50/p95/p99 latency, CPU and memory observations when available.

### B03 TCP Concurrency
Repeat B02 over DNS/TCP including connection setup and teardown behaviour.

### B04 Registrar Persistence
Write domain/zone/record state, close the registrar service, reopen the persistent store and independently read state back. Compare pre-close and post-rehydrate canonical state hashes.

### B05 DNS Restart/Rehydration
Start authority, qualify representative answers, terminate cleanly, restart from persistent state and re-run SOA/NS/A/AAAA/CNAME/MX/TXT/CAA and NXDOMAIN checks.

### B06 Failure Paths
At minimum test:
- malformed DNS packets;
- unsupported/invalid query forms;
- bind conflict on TCP 53;
- bind conflict on UDP 53;
- missing persistence store;
- inaccessible persistence store when safely reproducible;
- duplicate record/state operations;
- unknown domain/zone queries;
- guest/process termination during active workload where safely reproducible.

### B07 Persistence Integrity
Verify that persistent registrar/zone state survives process restart without silent loss or mutation. Record database hashes or canonical logical-state hashes before and after rehydration.

### B08 Network Vantage
Qualify loopback, non-loopback private-interface, and, once public substrate exists, external-vantage UDP/TCP reachability separately. Never infer one vantage from another.

### B09 Reference Comparison
Compare the measured properties with established authoritative DNS implementations or documented operational expectations. Structural similarity is not a performance claim. Record reference system/version, workload normalization and material differences.

## Required Metrics

For applicable benchmark groups record:

- benchmark ID;
- implementation commit(s);
- environment description;
- Python version;
- host CPU/memory information when observable;
- workload size;
- concurrency;
- successes;
- failures;
- throughput;
- min/max latency;
- p50/p95/p99 latency;
- restart duration where applicable;
- pre/post canonical state digests;
- environmental readback;
- raw evidence location;
- qualification conclusion.

## Qualification States

`INTERNALLY_TESTED` must not be promoted directly to `PRODUCTION_QUALIFIED`.

Required progression where applicable:

`INTERNALLY_TESTED -> REPEATED_RUN_QUALIFIED -> CONCURRENCY_QUALIFIED -> RESTART_REHYDRATION_QUALIFIED -> PERSISTENCE_QUALIFIED -> FAILURE_PATH_QUALIFIED -> EXTERNAL_COMPARISON_QUALIFIED -> PRODUCTION_QUALIFIED`

## Evidence Rule

Benchmark harness output is a candidate claim. Qualification is established by pre/post observation, persisted raw measurements, environmental readback, and comparison against the declared benchmark contract.
