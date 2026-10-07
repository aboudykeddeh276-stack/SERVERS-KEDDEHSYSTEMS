# KEDDEH editable authoring worktrees

Each primitive below is an independently versioned worktree: its own manifest, renderer, style layer, schema surface, and tests/validation contract. A container does not absorb the implementation of a link inside it; the link remains a child artifact with its own identity and code stack.

| Worktree | Purpose |
|---|---|
| link | governed navigation with safe protocol handling |
| button | accessible command trigger |
| execution | declarative action request; never arbitrary browser eval |
| heading | section hierarchy |
| title | page-level identity |
| photo | image, alt text, caption and source |
| container | layout and child ownership |
| name | named entity or capability |
| claim | assertion plus evidence status |
| learning | sourced observation plus confidence |

The authoring surface is in `worktrees/authoring-surface`. The fixed bottom-left “+” is an insertion control visible only in authenticated admin mode or explicitly chosen local-draft mode. Every artifact opens an inspector containing its property/code stack. Nested hyperlinks remain individually selectable/editable.

Production writes require the loopback authoring API behind an authenticating reverse proxy. Local-draft edits are durable only in the browser and can be exported as JSON; they do not silently mutate production.
