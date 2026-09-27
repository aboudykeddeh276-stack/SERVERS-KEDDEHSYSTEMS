# KEDDEH GitHub Agentic Access Workflows — 2026-09-28

## Purpose

This document defines technologically valid agentic access workflows for KEDDEH GitHub operations. It is written for the KEDDEH multi-account/team operating model and preserves the distinction between source control, CI, deployment, evidence, account authority, and public runtime effect.

GitHub is a versioned source and automation surface. GitHub success is not automatically DNS success, Sites deployment, public runtime success, or business-process execution.

## Core Rules

1. Never place secrets in source, issues, PRs, workflow logs, workbook cells, or email.
2. Every mutating GitHub action must identify actor, repo, branch/ref, target path, commit SHA, and intended effect.
3. Direct pushes to default branches are reserved for explicitly authorised emergency or owner-approved changes.
4. Normal agentic work uses branch -> commit -> PR -> review -> merge -> CI/deploy/readback.
5. GitHub Actions status is CI evidence only. It does not prove external deployment unless the deployment boundary is also observed.
6. A worker cannot be its own independent verifier.
7. Repo visibility, branch protection, environment protection, and secret scope are authority boundaries, not decorative settings.
8. Use least privilege: read-only for inventory, contents write for source changes, actions/deploy permissions only where needed.
9. Treat failed auth, 403, 404, missing repo, missing branch, and missing workflow as separate observations.
10. Preserve KEDDEH/BRAINK/KEX/ClaimPath/CasePath/source-domain distinctions. Do not collapse repos into one app.

## Known Repository Classes From Current Registry

| Repository | Registry role | Default use |
|---|---|---|
| `aboudykeddeh276-stack/BRAINK` | Canonical BRAINK runtime/source | Core BRAINK implementation, runtime, source binding |
| `aboudykeddeh276-stack/SERVERS-KEDDEHSYSTEMS` | KEDDEH server/runtime surface | Server estate, integration handoff, deployment/control workflows |
| `aboudykeddeh276-stack/BRAINK_DESKTOP_ORGANISED` | BRAINK replica/workstation | Workstation/reference; do not treat as canonical without binding |
| `aboudykeddeh276-stack/Braink-Beta` | BRAINK beta replica | Staging/reference candidate |
| `aboudykeddeh276-stack/BRAINK-CONSOLE-PLUS` | BRAINK console replica | HCI/console source candidate |
| `aboudykeddeh276-stack/kex-braink-substrate` | KEX/BRAINK substrate | KEX/BRAINK substrate source candidate |
| `aboudykeddeh276-stack/KEX_HYPERDRIVE_DASHBOARD_UI` | KEX UI/dashboard | KEX dashboard/UI candidate |
| `DOMAIN-AUTHORITY` | Named domain authority surface | Unresolved until exact repo identity is verified |

## Workflow 1 — Repository Inventory

Goal: discover what exists without mutating anything.

Steps:

1. Read repository metadata: visibility, default branch, permissions, archived state.
2. Read branches relevant to active work.
3. Read root files: README, package/build config, deployment config, `.github/workflows`, `.openai/hosting.json` where present.
4. Record current HEAD SHA and default branch.
5. Classify repo role: canonical, candidate, replica, historical, unresolved.

Evidence required:

- repo full name;
- metadata read timestamp;
- default branch;
- HEAD SHA or fetched file blob SHA;
- permission set observed;
- confidence class.

Do not infer deployment from source presence.

## Workflow 2 — Source Binding

Goal: bind a website/product/domain to exact source.

Steps:

1. Start from registry row: site slug/domain/source candidate.
2. Fetch candidate repo paths or Drive source bytes.
3. Compare source content to live/site/provider readback where available.
4. Record match, mismatch, historical candidate, or unresolved.
5. Update source-binding evidence only after readback.

States:

- `SOURCE_BYTES_OBSERVED`
- `CANDIDATE_NOT_CURRENT_BINDING`
- `CURRENT_RECENT_SOURCE_CANDIDATE`
- `PROJECT_IDENTITY_VERIFIED_SOURCE_UNRESOLVED`
- `PENDING_BINDING`
- `VERIFIED_CURRENT_BINDING`

## Workflow 3 — Branch Creation

Goal: isolate agentic work from default branch.

Branch naming:

```text
kex/<scope>-<yyyymmdd>
braink/<scope>-<yyyymmdd>
casepath/<scope>-<yyyymmdd>
claimpath/<scope>-<yyyymmdd>
site/<slug>-<scope>-<yyyymmdd>
```

Process:

1. Read default branch HEAD.
2. Create branch from default branch or exact commit SHA.
3. Record branch name and base SHA.
4. Do not reuse stale branches for unrelated work.

## Workflow 4 — File Create/Update/Delete

Goal: mutate source through GitHub contents API or Git CLI with explicit path-level evidence.

Create:

1. Confirm file path does not already exist.
2. Create file with commit message and branch.
3. Record resulting commit SHA.

Update:

1. Fetch file first.
2. Preserve blob SHA.
3. Apply replacement with that SHA.
4. Record resulting commit SHA and new blob SHA.

Delete:

1. Fetch file first.
2. Preserve blob SHA.
3. Delete only when explicitly authorised.
4. Record commit SHA.

No path should be updated from stale content without a current blob SHA.

## Workflow 5 — Pull Request

Goal: expose source mutation for review and integration.

1. Create PR from work branch to target branch.
2. PR body must include:
   - scope;
   - changed files;
   - evidence;
   - tests run;
   - external boundaries not crossed;
   - rollback plan;
   - next readback.
3. Request review from a distinct person/model/team where available.
4. Do not self-certify independent review.
5. Merge only after required checks/reviews.

## Workflow 6 — CI / GitHub Actions

Goal: use Actions as source/test automation evidence.

1. Read workflow files before interpreting results.
2. Trigger or wait for workflow run.
3. Record run ID, job IDs, conclusion, logs, and commit SHA.
4. Distinguish zero-step runner failure from pass/fail.
5. Treat unavailable logs as evidence gap, not success.

CI can establish build/test state for the commit. It does not establish public deployment unless deployment readback is included and observed.

## Workflow 7 — Release / Tag

Goal: mark a tested source state.

1. Tag only immutable source states.
2. Include changelog and evidence links.
3. Attach artifacts only when artifact bytes are generated from the tagged source or clearly labelled external companions.
4. Record tag SHA and release URL.

Do not tag unreviewed exploratory scratch work as production.

## Workflow 8 — Environment / Deployment From GitHub

Goal: deploy from source through protected environments.

1. Confirm environment name and protection rules.
2. Confirm secrets exist by name/scope only; never print values.
3. Deploy from exact commit SHA.
4. Capture deployment ID/run ID.
5. Read back target runtime/public URL.
6. Record rollback SHA/version.

Deployment evidence must include both GitHub deployment state and external runtime/readback state.

## Workflow 9 — Sites Deployment From GitHub Source

Goal: connect GitHub source to Sites production deployment without bypassing evidence.

Required chain:

```text
GitHub branch/commit -> pushed source state -> Sites version save -> Sites deploy -> production URL -> browser/readback -> evidence receipt
```

Rules:

- `.openai/hosting.json` project ID is authoritative when present.
- Do not create a second Site for an existing local site.
- Every Sites deployment URL is production.
- Preserve current audience unless explicitly changed.
- Deploy only saved versions.
- Do not equate GitHub commit with Sites production deployment.

## Workflow 10 — DNS / Domain Authority

Goal: modify DNS only after source/site readiness is proven.

Required before cutover:

1. Current DNS/mail snapshot: A/AAAA/CNAME/TXT/MX/SPF/DKIM/DMARC/CAA where applicable.
2. Registrar/DNS provider authority readback.
3. Staged site/version readback.
4. Rollback pointer.
5. Owner approval for cutover.
6. Post-change authoritative DNS query readback.
7. TLS validation readback.
8. HTTPS content match readback.

GitHub cannot prove DNS authority by itself.

## Workflow 11 — Issues / Work Queue

Goal: track work without confusing issue text for execution.

Issue fields should include:

- root/product;
- foundry/process area;
- source repo/path;
- target site/domain/runtime;
- dependencies;
- owner/worker;
- evidence required;
- blocker class;
- next discriminating test.

Issue state is coordination state only. It is not implementation proof.

## Workflow 12 — Security / Secrets

Allowed:

- reference secret names;
- verify whether required secret names exist if tooling permits;
- record missing/available secret state.

Forbidden:

- printing secret values;
- committing `.env` files;
- placing credentials in workbook cells, issues, PRs, emails, logs or reports;
- using a personal token where an app/least-privilege credential is required.

## Workflow 13 — Evidence Ledger

Every source mutation should produce an evidence event:

```json
{
  "repo": "owner/name",
  "branch": "branch",
  "commit_sha": "sha",
  "paths": ["..."],
  "actor": "account/tool/model",
  "intent": "...",
  "tests": "...",
  "external_effect": "none|observed",
  "readback": "...",
  "confidence": "OBSERVED|CORROBORATED|...",
  "next": "..."
}
```

## Current Branch Event

This workflow document was pushed to:

```text
repo: aboudykeddeh276-stack/SERVERS-KEDDEHSYSTEMS
branch: kex/site-estate-evidence-20260928
path: keddeh/github-agentic-access/GITHUB_AGENTIC_ACCESS_WORKFLOWS_20260928.md
```

This establishes GitHub source push for process documentation. It does not establish DNS/Sites production deployment.
