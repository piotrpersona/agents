#!/usr/bin/env bash
# Install this repo's Claude Code config into ~/.claude.
#
# Rules, hooks, skills and the status line are symlinked, so `git pull` updates them
# with no reinstall. settings.json is generated, because it has to combine the
# shared settings tracked here with the machine-local ones that are not.
#
#   curl -fsSL https://raw.githubusercontent.com/piotrpersona/agents/main/install.sh | bash
#
# Override with env vars:
#   AGENTS_DIR   where to clone   (default ~/developer/github.com/piotrpersona/agents)
#   AGENTS_REPO  clone source
#   CLAUDE_DIR   config target    (default $CLAUDE_CONFIG_DIR, else ~/.claude)
set -euo pipefail

AGENTS_REPO=${AGENTS_REPO:-https://github.com/piotrpersona/agents.git}
AGENTS_DIR=${AGENTS_DIR:-$HOME/developer/github.com/piotrpersona/agents}
CLAUDE_DIR=${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}
STAMP=$(date +%Y%m%d-%H%M%S)

say()  { printf '  %s\n' "$*"; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

for dep in git jq; do
  command -v "$dep" >/dev/null || die "$dep is required but not installed"
done

# 1. get the repo. If install.sh is being run from inside a clone, use that.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)
if [ -n "$here" ] && [ -f "$here/settings.shared.json" ]; then
  AGENTS_DIR=$here
  say "using clone at $AGENTS_DIR"
elif [ -d "$AGENTS_DIR/.git" ]; then
  say "updating $AGENTS_DIR"
  git -C "$AGENTS_DIR" pull --ff-only --quiet
else
  say "cloning into $AGENTS_DIR"
  mkdir -p -- "$(dirname -- "$AGENTS_DIR")"
  git clone --quiet "$AGENTS_REPO" "$AGENTS_DIR"
fi

mkdir -p -- "$CLAUDE_DIR/rules" "$CLAUDE_DIR/hooks" "$CLAUDE_DIR/skills"

# 2. symlink, moving any real file aside first so nothing is lost
link() { # $1=source in repo  $2=target under CLAUDE_DIR
  local src=$1 dst=$2
  if [ -L "$dst" ]; then
    [ "$(readlink -- "$dst")" = "$src" ] && return 0
    rm -- "$dst"
  elif [ -e "$dst" ]; then
    mv -- "$dst" "$dst.$STAMP.bak"
    say "backed up $(basename -- "$dst") -> $(basename -- "$dst").$STAMP.bak"
  fi
  ln -s -- "$src" "$dst"
  say "linked $(basename -- "$dst")"
}

for f in "$AGENTS_DIR"/rules/*.md;  do link "$f" "$CLAUDE_DIR/rules/$(basename -- "$f")"; done
for f in "$AGENTS_DIR"/hooks/*.sh;  do link "$f" "$CLAUDE_DIR/hooks/$(basename -- "$f")"; done
for d in "$AGENTS_DIR"/skills/*/;  do link "${d%/}" "$CLAUDE_DIR/skills/$(basename -- "$d")"; done
link "$AGENTS_DIR/statusline.sh" "$CLAUDE_DIR/statusline.sh"

# 3. settings.json = shared (tracked) deep-merged with machine-local (untracked)
machine=$CLAUDE_DIR/settings.machine.json
if [ ! -f "$machine" ]; then
  cp -- "$AGENTS_DIR/settings.machine.example.json" "$machine"
  say "created $machine from the example - edit it for this machine"
fi

settings=$CLAUDE_DIR/settings.json
merged=$(jq -s -f "$AGENTS_DIR/merge.jq" "$AGENTS_DIR/settings.shared.json" "$machine") \
  || die "could not merge settings; is $machine valid JSON?"

if [ -f "$settings" ] && [ "$(jq -S . <<<"$merged")" = "$(jq -S . "$settings" 2>/dev/null)" ]; then
  say "settings.json already current"
else
  [ -f "$settings" ] && cp -- "$settings" "$settings.$STAMP.bak" \
    && say "backed up settings.json -> settings.json.$STAMP.bak"
  printf '%s\n' "$merged" > "$settings"
  say "wrote settings.json"
fi

printf '\ndone. Restart Claude Code to pick up hook and settings changes.\n'
