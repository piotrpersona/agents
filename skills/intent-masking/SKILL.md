---
name: intent-masking
description: Use before any MCP tool call (`mcp__*`) whose arguments include a
  free-text intent, purpose, reason, rationale, justification or session_intent
  field — decides whether that field has to be sent at all, and mints a UUIDv4
  token to send in place of the text. Also triggers on "intent masking", "mask
  the intent", or questions about what a masked token stood for.
---

# Intent masking

No intent text, reasoning excerpt or PII ever leaves this machine inside an MCP
tool argument. Either the field is dropped, or it carries a UUIDv4 token whose
meaning stays in a local ledger.

Run this before the call, not after — once an argument is sent it cannot be
unsent.

## Step 1 — is the field required?

Read the tool's JSON schema in its tool definition and look at `required`.

- **Field absent from `required`** → omit the key completely. Do not send `""`,
  `"n/a"`, `null` or a token. This is the common case.
- **Field listed in `required`** → go to step 2. Never satisfy it with text.

## Step 2 — mint a token

Always name the operation. The first call under a label mints a token; every
later call under that same label in this session gets the same token back, so a
stateful server still sees one correlated operation instead of a stream of
unrelated UUIDs. Do not try to remember the UUID between turns — ask for it
again by label.

```sh
python3 ~/.claude/skills/intent-masking/mask_intent.py mask --tool <tool_name> --operation <label>
```

Pass the printed UUID verbatim as the field's value. Use one short kebab-case
label per user-visible operation (`audit-ledger`, `deploy-check`), a new one
when the operation changes. Dropping `--operation` mints a fresh token on every
call, which is right for a genuinely one-off call and wrong for anything with
follow-ups.

To keep the real intent for later audit, feed it on stdin so it never appears
in a process argument list. Only the call that mints the token records it:

```sh
python3 ~/.claude/skills/intent-masking/mask_intent.py mask --tool <tool_name> --operation <label> --intent - <<'EOF'
<intent text>
EOF
```

Labels do not cross sessions — a new session mints a fresh token for the same
label, which keeps a server from correlating your work across sessions.

## Step 3 — validate before sending

```sh
python3 ~/.claude/skills/intent-masking/mask_intent.py check <value>
```

Exits 0 for a strict RFC 4122 UUIDv4, 1 for anything else. Use it whenever a
token arrives from somewhere other than step 2 — session context, a previous
turn, the user.

## What never gets masked

Only fields that exist to describe *why* a call is made. A field the tool needs
semantically breaks when masked, so leave it alone and keep user context out of
it instead:

- search queries, paths, symbol names, code, SQL
- pagination cursors and auth tokens — a field named `token` is usually one of
  these, not an intent
- `limit`, `dry_run` and other non-PII primitives

Never move intent text or PII into a neighbouring metadata field to get around
a dropped `intent`.

## Audit

Read the trail when you need to know what this session masked — after
compaction, or when the user asks what a token stood for. It needs no UUID in
hand, which is the point:

```sh
python3 ~/.claude/skills/intent-masking/mask_intent.py trail
python3 ~/.claude/skills/intent-masking/mask_intent.py trail --operation <label>
python3 ~/.claude/skills/intent-masking/mask_intent.py trail --all --limit 50
```

One line per record: `created_at | intent_id | operation | tool | intent`.
Scoped to this session unless `--all`. With a UUID already in hand, the full
record comes from:

```sh
python3 ~/.claude/skills/intent-masking/mask_intent.py resolve <intent_id>
```

Exits 1 if the token was minted elsewhere.

The ledger is `~/.claude/intent-masking/ledger.jsonl` (dir `0700`, file
`0600`), append-only, local. `CLAUDE_CONFIG_DIR` moves it;
`INTENT_MASKING_DIR` overrides it outright. The MCP server cannot read it, so
the token is opaque on the wire by design — hydration, when a server supports
it, is wired out of band and never through the tool argument.
