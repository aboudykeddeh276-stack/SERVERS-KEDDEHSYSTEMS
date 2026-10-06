$TTL 300
@ IN SOA ns1.keddeh.com. hostmaster.keddeh.com. (
  2026100601 ; serial
  300        ; refresh
  120        ; retry
  1209600    ; expire
  300        ; minimum
)

@    IN NS ns1.keddeh.com.
@    IN NS ns2.keddeh.com.

; Replace these with the real static public IPv4 addresses after server provisioning.
ns1  IN A NS1_STATIC_IPV4
ns2  IN A NS2_STATIC_IPV4

; Managed Sites frontage targets currently required for keddeh.com.
@    IN A 162.159.143.30
@    IN A 172.66.3.26

_openai-site-verification IN TXT "openai-site-verification=9bTkxyG5KBvN0H0lfANAd2g39F5y583SKhU4NM1AeLo"
_cf-custom-hostname IN TXT "1f00240e-46e2-4c6c-afee-08c61519df0b"

; Mail is deliberately not configured here. Preserve existing MX/SPF/DKIM/DMARC records before delegation.
