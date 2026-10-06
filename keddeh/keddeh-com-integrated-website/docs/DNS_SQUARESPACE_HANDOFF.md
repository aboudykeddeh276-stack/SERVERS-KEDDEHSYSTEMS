# KEDDEH.com Squarespace / DNS Handoff

## Current managed Sites attachment

`keddeh.com` is attached to the KEDDEH Workspace Site.

- Sites project: `appgprj_6aaa7bfa99f08191a7dc892e2df3406f`
- Custom domain id: `appgdom_6ac45502289081919fe387dac9b63595`
- Status: `pending`
- SSL status: `pending_validation`

## If using ChatGPT Sites as the current web frontage

Add these records in Squarespace DNS exactly.

| Host/name | Type | Value |
|---|---|---|
| `@` | A | `162.159.143.30` |
| `@` | A | `172.66.3.26` |
| `_openai-site-verification` | TXT | `openai-site-verification=9bTkxyG5KBvN0H0lfANAd2g39F5y583SKhU4NM1AeLo` |
| `_cf-custom-hostname` | TXT | `1f00240e-46e2-4c6c-afee-08c61519df0b` |

Do not add an apex CNAME for `keddeh.com`.

## If routing `www.keddeh.com`

DNS cannot route by path. A CNAME for `www` moves the whole `www.keddeh.com` host to the selected target.

- For ChatGPT Sites frontage, use the Sites-provided CNAME target when the hostname is attached.
- For Railway frontage, use the Railway-provided CNAME target.
- Do not point `www` at Railway if the intended public website currently lives on ChatGPT Sites unless you are intentionally moving the full host.

## If switching to KEDDEH-operated nameservers

You need two public hosts with static IP addresses before Squarespace can delegate the domain safely.

Required values to obtain from your server provider:

| Nameserver | Required data |
|---|---|
| `ns1.keddeh.com` | static public IPv4, UDP/TCP 53 reachable |
| `ns2.keddeh.com` | static public IPv4, UDP/TCP 53 reachable on a separate host or failure domain |

Only after both hosts answer authoritatively should Squarespace registrar nameservers/glue be changed to:

```text
ns1.keddeh.com -> NS1_STATIC_IPV4
ns2.keddeh.com -> NS2_STATIC_IPV4
```

## External verification commands

```bash
dig @NS1_STATIC_IPV4 keddeh.com SOA
dig @NS1_STATIC_IPV4 keddeh.com SOA +tcp
dig @NS2_STATIC_IPV4 keddeh.com SOA
dig @NS2_STATIC_IPV4 keddeh.com SOA +tcp
dig keddeh.com NS
```

## Current blocker

The public nameserver addresses cannot be truthfully supplied until the two public server hosts exist and their static IPs are known. This repository includes the server package; it does not invent unprovisioned IP addresses.
