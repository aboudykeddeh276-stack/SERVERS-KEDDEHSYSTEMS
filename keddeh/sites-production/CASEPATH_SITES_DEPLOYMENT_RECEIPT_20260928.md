# CasePath Sites Production Deployment Receipt - 2026-09-28

## Entity / Artifact
- Site: `casepath-legal`
- Title: `CasePath Legal Preparation`
- Project ID: `appgprj_6a714946ab5c819187d5a9cbb22406d4`
- Version ID: `appgprj_6a714946ab5c819187d5a9cbb22406d4~appgver_6e6732be2b7c8191a90e2299d9d5e359`
- Version number: `71`
- Source commit: `e6392623a5b27b271e784b9e1f758fe90a20328f`
- Archive hash: `sha256:e888e384e793749b84b8cf997023da6c4fbaaae21130a6417ef971334a21cdc4`

## Observation
The latest saved CasePath site version was deployed to Sites production.

## Execution Boundary
- Sites deployment operation: `deploy_site_version`
- Deployment ID: `appgdep_6ab9620877948191b5ffaf51041fd62d`
- Status: `succeeded`
- Production URL: `https://casepath-legal.aboudykeddeh276.chatgpt.site`
- Provider deployment ID: `aboudykeddeh276--casepath-legal`
- Updated at: `2026-09-27T18:36:12.278829+00:00`

## Custom Domain State
Custom domain: `casepath.com.au`

Refresh readback immediately before production deployment:
- Custom domain ID: `appgdom_6a8e24985e6c8191b8d891e7379f7e45`
- Status: `pending`
- Provider status: `pending`
- SSL status: `pending_validation`
- CNAME target: `custom-domains.chatgpt.site.`
- Apex A targets: `162.159.143.30`, `172.66.3.26`
- Required TXT: `_openai-site-verification.casepath.com.au = openai-site-verification=eLRnMDtBmsi6xwKJRKVM4B9amtiNx2TUb8Q3rbCYWKE`
- Required TXT: `_cf-custom-hostname.casepath.com.au = 9dac75b1-683a-42a1-bd19-2e256829384d`

## Evidence Class
- Sites production deployment: `OBSERVED`
- Platform URL live deployment: `CORROBORATED` by Sites deployment response
- Custom domain effect: `NOT_YET_DEMONSTRATED`
- DNS validation: `BLOCKED_PENDING_DNS_RECORDS`

## What This Establishes
- CasePath has a successful Sites production deployment for version 71.
- The deployed version is bound to source commit `e6392623a5b27b271e784b9e1f758fe90a20328f` and archive hash `sha256:e888e384e793749b84b8cf997023da6c4fbaaae21130a6417ef971334a21cdc4`.
- The production platform URL is active according to Sites deployment response.

## What This Does Not Establish
- It does not establish that `casepath.com.au` resolves to the deployed Site.
- It does not establish DNS provider records are installed.
- It does not establish independent user-value verification or consuming-department acknowledgement.

## Next Discriminating Test
1. Install or confirm DNS records for `casepath.com.au` at the DNS provider.
2. Refresh custom domain status until `status`, `provider_status`, and `ssl_status` clear pending validation.
3. Obtain downstream consumer acknowledgement that the CasePath workflow surface is ingested and reduces end-user friction.
4. Route any critique through IT Feedback / Progressive Team Review.