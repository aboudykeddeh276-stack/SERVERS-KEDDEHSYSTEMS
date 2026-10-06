# KEDDEH.com Integrated Website and Server Authority Package

This package is the source-controlled build surface for `keddeh.com`, KEDDEH server authority, skill execution packaging, DNS handoff, and VFS-backed storage integration.

## What this package is

- A full static website profile for KEDDEH.com.
- A repository build surface that can be copied into a new standalone repository when a repo-creation actuator is available.
- A DNS and nameserver launch kit for owner-controlled Linux hosts.
- A Squarespace handoff with the exact records currently known from Sites plus the requirements for switching to KEDDEH-operated nameservers.
- A skill authority explanation that separates authored skill source from installed ChatGPT runtime execution.

## What this package is not claiming yet

- It does not claim public UDP/TCP 53 nameservers are live until public hosts with static IP addresses are provisioned and externally observed.
- It does not claim `keddeh.com` TLS is active while Sites reports `pending_validation`.
- It does not claim ChatGPT chat can execute arbitrary local skills until those skills are installed/admitted into the chat runtime or exposed through an authorized connector/MCP/server boundary.

## Current verified authority

- GitHub repository: `aboudykeddeh276-stack/SERVERS-KEDDEHSYSTEMS`
- Current GitHub principal has admin/write authority on this repository.
- KEDDEH.com is attached in Sites to project `appgprj_6aaa7bfa99f08191a7dc892e2df3406f` as custom domain `appgdom_6ac45502289081919fe387dac9b63595`.
- KEDDEH.com status at last readback: `pending`, SSL `pending_validation`.

## Directory map

- `index.html` — integrated KEDDEH.com website profile.
- `docs/SKILLS_EXECUTION_AUTHORITY.md` — exact answer to what blocks authored skills from executing inside ChatGPT chat.
- `docs/DNS_SQUARESPACE_HANDOFF.md` — what to set in Squarespace or any registrar/DNS provider.
- `server/docker-compose.yml` — BIND authoritative DNS server launch scaffold.
- `server/named.conf` — BIND authoritative server configuration.
- `server/zones/db.keddeh.com` — starting zone file for KEDDEH.com.
- `server/vfs-storage/README.md` — VFS/storage integration boundary.

## Launch sequence

1. Publish the website source through the selected web hosting surface.
2. For the managed Sites path, publish the exact A and TXT records listed in `docs/DNS_SQUARESPACE_HANDOFF.md`.
3. For KEDDEH-operated DNS, provision two public Linux hosts with static IPv4 addresses.
4. Copy `server/` to both hosts, set the real `NS1_IPV4` and `NS2_IPV4` values in the zone file, then launch with Docker Compose.
5. Confirm each server answers authoritative UDP and TCP 53 for `keddeh.com`.
6. Only after both nameservers pass external readback, change registrar nameservers in Squarespace to `ns1.keddeh.com` and `ns2.keddeh.com` with matching glue records.

## Minimum proof before calling nameservers live

```bash
dig @NS1_IPV4 keddeh.com SOA +tcp
dig @NS1_IPV4 keddeh.com NS
dig @NS2_IPV4 keddeh.com SOA +tcp
dig @NS2_IPV4 keddeh.com NS
```

Then verify from independent public resolvers after parent delegation changes propagate.
