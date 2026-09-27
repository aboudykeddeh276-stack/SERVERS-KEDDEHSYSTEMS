# KEDDEH Site Estate Evidence Handoff — 2026-09-28

## Scope

This branch records the current KEDDEH site/source-boundary evidence package and a local non-production DomainState runtime-adapter boundary.

This is a GitHub source push. It is not a DNS cutover, Sites production deployment, account-membership mutation, credential mutation, or public-domain authority claim.

## Account Boundary

- Current sender/tooling principal observed: `aboudykeddeh276@gmail.com`
- KEDDEH receiving/team account used for email and Library sharing: `aboudy@keddeh.com`
- Canonical workbook metadata read from the current principal returned `403 PERMISSION_DENIED`.
- That establishes current-principal access blocked only; it does not establish workbook absence or control-plane offline.

## Parsed Site Estate

The current registry extraction found:

- 7 site rows
- 8 domain/DNS rows
- 4 agent/account rows
- 13 migration queue rows
- 11 source-anchor rows
- 3 proof-ledger rows
- 8 repository rows
- 10 source-binding rows

Key site routes:

- `kex-geometric-address` — `https://kex-geometric-address.aboudykeddeh276.chatgpt.site`
- `claimpath-local` — `https://claimpath-local.aboudykeddeh276.chatgpt.site` — custom domain candidate `claimpath.com.au`
- `casepath-legal` — `https://casepath-legal.aboudykeddeh276.chatgpt.site` — custom domain candidate `casepath.com.au`
- `braink-keddeh-systems` — `https://braink-keddeh-systems.aboudykeddeh276.chatgpt.site`
- `keddeh-mining-btc` — `https://keddeh-mining-btc.aboudykeddeh276.chatgpt.site` — custom domain candidate `mining.keddeh.systems`
- `braink-systems` — `https://braink-systems.aboudykeddeh276.chatgpt.site`
- `kex-sovereign-capacity-fabric` — `https://kex-sovereign-capacity-fabric.aboudykeddeh276.chatgpt.site` — custom domain candidate `keddehsystems.com`

## GitHub Source Binding Context

Registry-verified repositories include:

- `aboudykeddeh276-stack/BRAINK`
- `aboudykeddeh276-stack/SERVERS-KEDDEHSYSTEMS`
- `aboudykeddeh276-stack/BRAINK_DESKTOP_ORGANISED`
- `aboudykeddeh276-stack/Braink-Beta`
- `aboudykeddeh276-stack/BRAINK-CONSOLE-PLUS`
- `aboudykeddeh276-stack/kex-braink-substrate`
- `aboudykeddeh276-stack/KEX_HYPERDRIVE_DASHBOARD_UI`

`DOMAIN-AUTHORITY` remains unresolved in the registry and must not be treated as verified until exact repository identity is resolved.

## DomainState Adapter Boundary

The branch includes a minimal local non-production runtime adapter for `KEX_DOMAIN_PROJECTION_REGISTRY_V1`.

It demonstrates:

- `DomainState.ingest(...)` invocation
- generation check
- duplicate operation rejection
- atomic JSON state write via replace
- ledger verification
- persisted state readback

Local test result before push:

```text
Ran 15 tests in 0.007s
OK
```

## What This Does Not Establish

This push does not establish:

- Sites production deployment
- DNS/TLS authority
- registrar control
- production runtime binding
- public domain effect
- independent assessment
- workbook-backed task claim

## Next Work

1. Resolve exact source binding for ClaimPath, KEDDEH.com frontage, BRAINK `braink.ai`, and KEX surfaces.
2. Push specific source changes into the appropriate verified source repositories.
3. Stage preview deployments before any DNS/Sites production cutover.
4. Require DNS/mail snapshot and independent DNS/TLS/HTTPS readback before domain promotion.
