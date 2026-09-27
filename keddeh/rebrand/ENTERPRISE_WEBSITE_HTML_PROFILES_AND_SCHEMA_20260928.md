# Enterprise Website HTML Profiles and Schema Requirements - 2026-09-28

## Purpose
Every KEDDEH website must be treated as its own enterprise-grade HTML profile, not as a loose page or disposable landing surface.

Each profile must preserve:
- market positioning
- user intent
- accessibility standards
- technical metadata
- structured data
- security/privacy posture
- source and deployment provenance
- DNS and routing state
- interconnectivity with the wider KEDDEH estate

## Global Enterprise Website Standard
Every KEDDEH website must include, at minimum:

### HTML / Metadata
- Valid HTML5 document structure.
- Unique `<title>` reflecting product and route intent.
- Unique meta description under 160 characters where possible.
- Canonical URL.
- Open Graph title, description, image, URL, and type.
- Twitter/X card metadata where applicable.
- Favicon and app icons.
- Language declaration.
- Viewport declaration.
- Robots policy appropriate to publication state.

### Accessibility and UX
- WCAG 2.2 AA target unless a stronger standard is required.
- Keyboard navigability.
- Logical heading hierarchy.
- Visible focus states.
- Sufficient color contrast.
- Alt text for meaningful images.
- Form labels and error messages.
- No essential workflow hidden behind hover-only interactions.
- Clear user-intent workflow, not status/plumbing-first copy.

### Performance and Core Web Vitals
- Optimized critical rendering path.
- Minimal blocking JS.
- Responsive layout for mobile/tablet/desktop.
- Stable layout with reduced shift.
- Image sizing and compression.
- Cache strategy for static assets.
- No unnecessary third-party scripts.

### Security / Trust / Compliance
- HTTPS only.
- Clear privacy/contact/legal links where product surface requires them.
- No exposed secrets, tokens, internal IDs, or private operational paths.
- Safe form handling and spam protection where forms exist.
- Separate public content from owner/team-only operations.

### Structured Data
Use JSON-LD where applicable:
- `Organization` for KEDDEH root and KEDDEH Systems.
- `SoftwareApplication` for software products and platforms.
- `WebSite` / `WebPage` for all published surfaces.
- `Service` for professional/productized services.
- `FAQPage` where FAQ content exists.
- `BreadcrumbList` for deep projection paths.

### Enterprise Provenance
Every site profile must record:
- owner/principal
- product/domain owner
- source repository or source artifact
- Sites project ID where applicable
- deployment URL
- custom domains
- current deployment version
- deployment receipt
- DNS validation state
- evidence confidence
- next discriminating test

## Canonical Parent Routing
`keddeh.com` is the authority root. Public projections should resolve under path-based routing unless a separate infrastructure boundary requires a subdomain.

Pattern:
- `keddeh.com/` - parent authority
- `keddeh.com/casepath` - CasePath product surface
- `keddeh.com/claimpath` - ClaimPath product surface
- `keddeh.com/braink` - BRAINK platform surface
- `keddeh.com/kex` - KEX execution framework surface
- `keddeh.com/systems` - KEDDEH Systems technical estate
- `keddeh.com/evidence` - public/private evidence index as appropriate
- `keddeh.com/status` - operational status as appropriate

## Per-Site Enterprise Profiles

### 1. KEDDEH Authority Root
- Public name: `KEDDEH`
- Canonical route: `https://keddeh.com/`
- Role: parent brand, trust anchor, portfolio entry, routing authority.
- Audience: clients, partners, team, platform users, assessors.
- Primary objective: explain KEDDEH as the parent enterprise and route users to product/platform surfaces.
- Required schema: `Organization`, `WebSite`, `WebPage`, `BreadcrumbList`.
- Required sections: identity, portfolio, trust/standards, products, platforms, contact/team route.
- Design standard: premium enterprise, restrained, high-trust, clear navigation.
- Interconnectivity: routes to CasePath, ClaimPath, BRAINK, KEX, Systems, Evidence/Status where published.
- Deployment boundary: DNS and host binding for `keddeh.com` must be confirmed before public go-live claim.

### 2. CasePath Legal
- Current Sites URL: `https://casepath-legal.aboudykeddeh276.chatgpt.site`
- Current custom domain: `casepath.com.au` pending validation.
- KEDDEH projection: `https://keddeh.com/casepath`
- Public name: `CasePath`
- Role: legal preparation and case workflow product.
- Audience: legal consumers, firms, advisors, support teams, case managers.
- Primary objective: convert legal complexity into clear guided preparation workflows.
- Required schema: `SoftwareApplication`, `Service`, `WebSite`, `WebPage`, `FAQPage` where applicable.
- Required sections: problem, workflow, intake, preparation, evidence handling, privacy/trust, call-to-action.
- Standards: accessibility-first, high trust, legal clarity, no unsupported legal advice claims.
- Interconnectivity: KEDDEH root, ClaimPath where claims intersect, evidence/status receipt where appropriate.
- Deployment state: Sites production deployment succeeded for version 71.
- DNS state: `casepath.com.au` pending validation.
- Next test: DNS validation and consumer readback.

### 3. ClaimPath
- Current Sites URL: `https://claimpath-local.aboudykeddeh276.chatgpt.site`
- Current custom domain: `claimpath.com.au` pending validation.
- KEDDEH projection: `https://keddeh.com/claimpath`
- Public name: `ClaimPath`
- Role: claims intake, routing, preparation, and support workflow product.
- Audience: claimants, advisors, support teams, operators.
- Primary objective: reduce claims friction by converting intent into structured intake and next actions.
- Required schema: `SoftwareApplication`, `Service`, `WebSite`, `WebPage`, `FAQPage` where applicable.
- Required sections: claim journey, intake steps, document/evidence requirements, support path, privacy/trust.
- Standards: plain-language workflow, mobile-first, accessible forms, measurable completion goals.
- Interconnectivity: KEDDEH root, CasePath where legal escalation applies, team feedback queue.
- Deployment state: latest version observed; no new deployment executed in this payload.
- DNS state: `claimpath.com.au` pending validation.
- Next test: deploy/redeploy latest production version and validate DNS records.

### 4. BRAINK Platform
- Current Sites URL: `https://braink-keddeh-systems.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/braink`
- Public name: `BRAINK`
- Role: intelligence/runtime platform under KEDDEH.
- Audience: technical evaluators, enterprise users, internal team, platform partners.
- Primary objective: present BRAINK as a coherent platform, not a scattered artifact set.
- Required schema: `SoftwareApplication`, `TechArticle` where docs exist, `WebSite`, `WebPage`.
- Required sections: platform overview, runtime model, use cases, integrations, security/trust, developer path.
- Standards: technical credibility, concise architecture explanation, no unsupported capability inflation.
- Interconnectivity: KEX, KEDDEH Systems, runtime/evidence/status paths.
- Next test: source binding to canonical BRAINK repo and deployment receipt.

### 5. BRAINK Systems
- Current Sites URL: `https://braink-systems.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/braink/systems`
- Public name: `BRAINK Systems`
- Role: systems/runtime-facing BRAINK estate.
- Audience: developers, operators, internal technical team.
- Primary objective: expose system capabilities, runtime structure, and integration pathways.
- Required schema: `SoftwareApplication`, `WebPage`, `BreadcrumbList`.
- Required sections: systems overview, runtime boundaries, integration points, evidence and deployment states.
- Standards: precise boundaries between local runtime, Sites production, DNS, and public domain effects.
- Next test: consolidate with BRAINK Platform or preserve as technical sub-surface.

### 6. KEX Execution Framework
- Current Sites URL: `https://kex-geometric-address.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/kex/geometric-address`
- Public name: `KEX Geometric Address Resolution`
- Role: KEX technical projection and execution concept surface.
- Audience: technical evaluators, developers, internal engineering team.
- Primary objective: explain KEX execution mechanics in usable, inspectable, evidence-bound terms.
- Required schema: `SoftwareApplication`, `TechArticle`, `WebPage`.
- Required sections: purpose, runtime model, address/projection concept, implementation evidence, limitations.
- Standards: technical exactness, falsifiable claims, clear non-production vs production boundaries.
- Next test: link to runtime adapter receipts and source repository.

### 7. KEDDEH Systems Development Centre
- Current Sites URL: `https://kex-sovereign-capacity-fabric.aboudykeddeh276.chatgpt.site`
- Custom domain candidate: `keddehsystems.com` pending.
- KEDDEH projection: `https://keddeh.com/systems/development-centre`
- Public name: `KEDDEH Systems Development Centre`
- Role: development, foundry, capacity, and systems coordination surface.
- Audience: enterprise partners, operators, engineering team.
- Primary objective: present the KEDDEH systems/foundry capability as enterprise-operational, not experimental clutter.
- Required schema: `Organization`, `Service`, `WebSite`, `WebPage`.
- Required sections: capabilities, foundries, governance, delivery workflows, contact/team route.
- Standards: enterprise assurance, governance clarity, source/deployment provenance.
- Next test: custom domain validation and source binding.

### 8. KEDDEH BTC Mining
- Current Sites URL: `https://keddeh-mining-btc.aboudykeddeh276.chatgpt.site`
- Custom domain candidate: `mining.keddeh.systems` pending.
- KEDDEH projection: `https://keddeh.com/mining`
- Public name: `KEDDEH Mining`
- Role: mining/runtime product or technical surface.
- Audience: technical/financial evaluators, partners, internal operators.
- Primary objective: present legitimate scope, operational state, and risk boundaries.
- Required schema: `Service`, `WebPage`, and compliance/legal disclaimers where applicable.
- Required sections: overview, operational model, evidence, risk disclosures, contact path.
- Standards: no investment claims without substantiation; explicit operational and jurisdictional boundaries.
- Next test: determine product/legal status before broad publication.

### 9. KEDDEH Workspace / Layered Linux Runtime
- Current Sites URL: `https://keddeh-layered-linux-runtime.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/workspace`
- Public name: `KEDDEH Workspace`
- Role: runtime/workstation/container capability surface.
- Audience: operators, developers, internal team.
- Primary objective: explain the workspace runtime and how it supports execution and deployment workflows.
- Required schema: `SoftwareApplication`, `WebPage`.
- Required sections: runtime overview, authority boundary, supported workflows, evidence/readback.
- Standards: avoid implying public production authority from internal runtime presence.
- Next test: bind to source repo/runtime manifest and execution receipt.

### 10. KEX Identity Service
- Current Sites URL: `https://kex-identity-service.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/identity`
- Public name: `KEDDEH Identity` or `KEX Identity Service`
- Role: identity and conditional registration surface.
- Audience: users, operators, developers.
- Primary objective: provide clear identity, registration, and access flow boundaries.
- Required schema: `SoftwareApplication`, `WebPage`.
- Required sections: sign-in/register path, privacy, authority, support, technical boundaries.
- Standards: security-first copy, privacy clarity, no token exposure.
- Next test: confirm active identity flow and privacy/compliance copy.

### 11. BRAINK Public Runtime
- Current Sites URL: `https://braink-public-runtime.aboudykeddeh276.chatgpt.site`
- KEDDEH projection: `https://keddeh.com/braink/runtime`
- Public name: `BRAINK Public Runtime`
- Role: public runtime demonstration or access surface.
- Audience: technical evaluators, users, partners.
- Primary objective: expose runtime value without overclaiming production authority.
- Required schema: `SoftwareApplication`, `WebPage`.
- Required sections: what it does, how to use it, runtime status, limitations, evidence links.
- Standards: precise runtime claims, no internal credential exposure.
- Next test: independent runtime readback and source provenance.

## Enterprise Implementation Checklist
For each website:
1. Create/update a single HTML profile specification.
2. Create/update JSON-LD schema block.
3. Verify metadata and canonical route.
4. Verify responsive layout and accessibility.
5. Verify privacy/contact/legal requirements.
6. Bind to source repository or source artifact.
7. Deploy through Sites or confirmed host.
8. Validate DNS/custom domain where applicable.
9. Preserve deployment receipt.
10. Route evidence to team and workbook surfaces.
11. Request independent value-target readback.

## Next Execution Order
1. `keddeh.com` parent site/profile.
2. CasePath already production-deployed: complete DNS validation and path projection.
3. ClaimPath production redeploy and DNS validation.
4. BRAINK platform consolidation.
5. KEX technical profile.
6. Systems/development-centre profile.
7. Remaining runtime/mining/identity surfaces after source/legal boundary review.

## Boundary State
- Enterprise profile instruction set: `EXECUTED_AS_GITHUB_SOURCE_PUSH`
- HTML implementation for each site: `NOT_YET_EXECUTED`
- DNS mutation: `NOT_EXECUTED`
- Sites production deployment: `CASEPATH_SUCCEEDED`; others require per-site execution
- Independent consumer value verification: `PENDING`