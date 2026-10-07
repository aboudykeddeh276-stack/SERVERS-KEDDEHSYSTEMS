# Authoring surface

This is an editable, source-visible KEDDEH workspace—not a general-purpose browser code executor.

- The fixed bottom-left “+” inserts a new independently identified primitive.
- Selecting any artifact opens its JSON code stack.
- Links nested in containers remain child artifacts with their own revisions.
- Local draft mode persists to browser storage and exports a complete JSON document.
- Authenticated admin mode reads/writes through `/api/document` with an ETag. Conflicting revisions receive HTTP 412.
- “Execution” is a declarative action identifier and input object. The browser never evaluates arbitrary JavaScript from document content.

## Production auth boundary

Run `server.py` on loopback only. The reverse proxy must remove all client-supplied `X-Keddeh-*` headers, complete the owner's passkey/authentication flow, then inject:

```
X-Keddeh-Auth-Verified: 1
X-Keddeh-Admin: <verified subject>
```

Never expose port 8787 directly. The backend does not accept a browser-stored master secret.

## Run locally

```bash
python3 worktrees/authoring-surface/server.py
# serve repository root separately and proxy /api to 127.0.0.1:8787
```
