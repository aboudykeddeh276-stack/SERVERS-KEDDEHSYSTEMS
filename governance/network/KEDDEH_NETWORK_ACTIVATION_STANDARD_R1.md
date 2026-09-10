# Keddeh Systems Network Activation Standard R1

## Purpose

This document governs promotion of Keddeh networking from code/configuration to observed live infrastructure. It deliberately reuses public Internet operational practice instead of inventing replacement procedures where mature standards exist.

## Authority and authorship

Integration architecture and Keddeh-specific control/proof composition: Keddeh Systems / Aboudy Keddeh.

External standards remain authored and governed by their issuing bodies. Keddeh Systems does not claim authorship of IETF RFCs, APNIC policy, NIST publications, ETSI standards, RPKI, BGP, DNSSEC or other third-party specifications.

## Reference baseline

- RFC 4271: BGP-4 protocol baseline.
- RFC 7454 / BCP 194: BGP operations and security.
- RFC 8212: eBGP import/export defaults must fail closed when policy is absent.
- RFC 6811 / RFC 7115 family and current RPKI operational practice: Route Origin Validation.
- RFC 4033, RFC 4034, RFC 4035 and RFC 6781: DNSSEC protocol and operational practice.
- RFC 2827 / BCP 38 and RFC 3704 / BCP 84: source-address validation / anti-spoofing.
- RFC 6241 and RFC 7950: NETCONF/YANG-style modeled configuration and state separation.
- RFC 5880: BFD-style rapid liveness detection where supported.
- APNIC Internet Number Resource Policies: public ASN, IPv4 and IPv6 resource eligibility and use in the Asia-Pacific region.
- NIST IR 8259 Rev.1, NIST IR 8259A and 8259B: IoT product/device cybersecurity activities and capabilities.
- ETSI EN 303 645: consumer IoT cybersecurity baseline where applicable.

## State model

No layer inherits the state of the layer before it.

DEFINED -> IMPLEMENTED -> STATICALLY_VALIDATED -> INTEGRATION_PROVEN -> HOST_PROVEN -> NETWORK_PROVEN -> FAILURE_PROVEN -> RECOVERY_PROVEN -> PROVEN_LIVE

`ACTIVE`, `READY`, `CONNECTED`, `CONFIGURED`, a PID, or a successful local unit test are never synonyms for `PROVEN_LIVE`.

## Virtual backbone gate

`VIRTUAL_BACKBONE_READY` may use private address space and private ASNs. It requires:

1. persistent node identity;
2. authoritative desired/observed state separation;
3. authenticated peer messages;
4. TLS for every non-loopback mesh listener;
5. a trusted CA for every non-loopback peer session;
6. fresh peer heartbeat and expiry;
7. inbound and outbound TCP probes;
8. persistent DA/registrar state outside the deployed code tree;
9. UDP and TCP DNS probes;
10. append-only receipts with correlation and previous-proof linkage.

## Public AS candidate gate

`PUBLIC_AS_CANDIDATE` additionally requires real resource authority evidence:

- public ASN assigned for the operator's network;
- public IPv4 and/or IPv6 resources with documented right-to-use;
- at least one intended upstream/IXP/inter-AS relationship;
- contacts and abuse/security escalation procedures;
- authoritative prefix inventory;
- explicit import/export policy model;
- routing registry/RPKI plan.

Private/documentation ASN or TEST-NET/example prefixes are rejected from this state.

## Global edge gate

`GLOBAL_EDGE_READY` requires all of the above plus:

1. explicit import policy per eBGP neighbor;
2. explicit export policy per eBGP neighbor;
3. exact owned-prefix export allow-list;
4. max-prefix limits appropriate to each session;
5. bogon/martian and own-prefix ingress filtering;
6. source-address validation at customer/access edges;
7. ROAs matching intended originated prefixes;
8. ROV monitoring before reject-invalid enforcement, then reject-invalid after validation;
9. redundant RPKI validator plan where ROV is enabled;
10. BGP session protection appropriate to the peer;
11. peer liveness and route-state telemetry;
12. rollback configuration and console/out-of-band recovery path;
13. staged bring-up: session -> receive -> validate -> limited advertise -> observe -> full policy;
14. externally observed route evidence before `PROVEN_LIVE`.

No configuration may disable RFC 8212 fail-closed eBGP policy behavior as a shortcut to activation.

## DNS / DA gate

`DNS_DA_PROVEN_LIVE` requires:

- persistent registrar database outside application deployment directories;
- WAL/busy-timeout or equivalent concurrent-write protection;
- authoritative zone readback;
- mutation -> DNS observation -> readback proof;
- UDP query success;
- TCP query success;
- externally reachable authority proof for public DNS;
- DNSSEC key/signing/rollover policy before claiming DNSSEC capability;
- monotonically managed zone serials;
- backup/restore and corruption test;
- no publication of loopback/wildcard placeholder addresses as production authority records.

## IoT admission profile

IoT devices do not inherit HOST_READY merely because they are reachable. `IOT_DEVICE_READY` requires a device-specific admission profile covering at least:

- unique device identity;
- authorized configuration mechanism;
- protected stored/transmitted data as applicable;
- logical access/interface restriction;
- secure software/firmware update capability;
- cybersecurity state awareness/telemetry;
- lifecycle/support metadata;
- credential rotation/revocation;
- network segmentation policy;
- observed heartbeat and stale expiry.

## BRAINK / IL-LLM integration law

IL-LLM is used as the normalization/indexing layer for network intents and evidence. It does not replace protocol standards.

Every network request is normalized to one bounded envelope before leaving the BRAINK/KEX wrapper:

identity -> capability -> authority -> target host/node -> desired state -> protocol adapter -> execute -> observed state -> readback -> proof -> reconciliation.

Adapters may be BGP/FRR, DNS, registrar, TCP, NETCONF/YANG, Desktop Commander, systemd or device-specific interfaces. The normalized control/proof contract remains constant while the transport varies.

## Promotion law

Promotion follows observed evidence, never configuration intent. A failed or unavailable runner, carrier, peer, authority, certificate, RPKI validator or upstream keeps the associated state below the gate it cannot prove.
