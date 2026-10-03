#!/usr/bin/env bash
# SessionStart: notice git repos that have no CodeGraph index yet.
# Silence a repo by adding its root path to ~/.claude/codegraph-optout.
set -uo pipefail

optout=${CLAUDE_CONFIG_DIR:-$HOME/.claude}/codegraph-optout

input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[ -n "$cwd" ] || cwd=$PWD

command -v codegraph >/dev/null 2>&1 || exit 0

root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$root" ] || exit 0
[ -d "$root/.codegraph" ] && exit 0
[ -f "$optout" ] && grep -Fxq "$root" "$optout" && exit 0

jq -n --arg root "$root" --arg optout "$optout" '{
  systemMessage: "No CodeGraph index in \($root) — run `codegraph init` to enable codegraph_explore here, or `echo \($root) >> \($optout)` to stop asking.",
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: "This git repository (\($root)) has no .codegraph/ index, so CodeGraph tools are unavailable here. Indexing is the user'"'"'s decision: offer `codegraph init` once if code search comes up, and do not run it unprompted. If the user declines, offer to append the repo root to \($optout) so the check stays quiet for this repo."
  }
}'
