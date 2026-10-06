# KEDDEH Nameserver Launch

## Required before launch

Provision two public Linux servers with static IPv4 addresses:

- `ns1.keddeh.com` -> `NS1_STATIC_IPV4`
- `ns2.keddeh.com` -> `NS2_STATIC_IPV4`

Both servers must allow inbound UDP and TCP port 53.

## Configure

Edit `zones/db.keddeh.com` and replace:

```text
NS1_STATIC_IPV4
NS2_STATIC_IPV4
```

with the real server addresses.

Increment the SOA serial after every zone edit.

## Start

```bash
docker compose up -d
```

## Local host validation

```bash
docker compose ps
docker exec keddeh-authoritative-dns named-checkconf /etc/bind/named.conf
docker exec keddeh-authoritative-dns named-checkzone keddeh.com /etc/bind/zones/db.keddeh.com
```

## External validation before Squarespace delegation

Run from outside the DNS host network:

```bash
dig @NS1_STATIC_IPV4 keddeh.com SOA
dig @NS1_STATIC_IPV4 keddeh.com SOA +tcp
dig @NS2_STATIC_IPV4 keddeh.com SOA
dig @NS2_STATIC_IPV4 keddeh.com SOA +tcp
dig @NS1_STATIC_IPV4 keddeh.com A
dig @NS2_STATIC_IPV4 keddeh.com A
```

## Squarespace registrar step

Only after both nameservers answer externally, set registrar nameservers/glue:

```text
ns1.keddeh.com -> NS1_STATIC_IPV4
ns2.keddeh.com -> NS2_STATIC_IPV4
```

Do not change registrar delegation until the server readback passes. A repository package is not a public nameserver by itself.
