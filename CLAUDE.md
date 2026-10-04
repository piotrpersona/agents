# agents

Claude Code and Codex config: rules, hooks, skills, the status line and the
shared half of `settings.json`. See `README.md` for the layout.

`install.sh` symlinks everything into `~/.claude`, so a `git pull` rolls out a
change with no reinstall. `settings.json` is the one exception: it is
**generated** by merging `settings.shared.json` (tracked here) with
`settings.machine.json` (untracked, machine-local, holds absolute paths).

## Always check for drift before install.sh or make install

`install.sh` writes into `$HOME`. Never run it as the first step. Run the
check below, report what it found, and get approval before anything
destructive.

```sh
git status --short --branch                                   # uncommitted work here
git fetch -q origin && git log --oneline HEAD..origin/main    # incoming commits
make diff                                                     # live settings.json vs repo + machine overlay
```

Then audit every link target, because `install.sh` moves a real file aside but
never reports it in advance:

```sh
CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
for src in rules/*.md hooks/*.sh skills/*/ statusline.sh; do
    src=${src%/}; dst=$CLAUDE_DIR/$src
    if [ -L "$dst" ]; then
        [ -e "$dst" ] || { echo "dangling  $dst"; continue; }
        [ "$(readlink -- "$dst")" = "$PWD/$src" ] || echo "relink    $dst -> $(readlink -- "$dst")"
    elif [ -e "$dst" ]; then
        echo "REAL FILE $dst"
    else
        echo "new       $dst"
    fi
done
find "$CLAUDE_DIR" -maxdepth 2 -type l ! -exec test -e {} \; -print   # orphans
```

### What drift means here

| Finding | What the installer does | Report as |
| --- | --- | --- |
| `REAL FILE` at a link target | moved to `<target>.<stamp>.bak`, then replaced by a link | **destructive** — `diff` it against the repo copy and list what is only in the live file |
| `relink` to another path | the old link is removed and replaced | safe for files, but say which clone stops being live |
| `make diff` shows changes | `settings.json` is backed up, then overwritten | **destructive** — show the diff; a hand edit to the live file is lost unless it moves into `settings.shared.json` or `settings.machine.json` |
| `settings.machine.json` missing | created from `settings.machine.example.json` | safe, but the example has placeholder paths — say they need editing |
| `dangling` or orphan links | nothing; `install.sh` never removes a link | report them, they are left over from a renamed or deleted skill, hook or rule |
| `new` targets | a new link | no action |
| uncommitted changes here | `install.sh` links the working tree as-is | say the live config will include uncommitted work |

A `.bak` copy is a recovery path, not permission. Anything that moves, removes
or overwrites a file in `$HOME` is reported first and run second.

Never overwrite or regenerate an existing `settings.machine.json`. It is
untracked and machine-specific, so there is no copy in git to restore from.

### Report format

State, in this order: uncommitted files, incoming commits, the `make diff`
result, the link audit, then a plain list of every destructive action with its
recovery path. If the lists are empty, say the install is a no-op.

## Rules for changes

- Shared settings go in `settings.shared.json`. Anything with an absolute path
  or a machine-local tool version goes in `settings.machine.example.json`, and
  never in the shared file.
- `settings.machine.json`, `*.bak`, `.codex/` and `.serena/` are gitignored.
  Never commit them, and never commit a secret or an API key.
- Arrays concatenate on merge (see `merge.jq`), so a hook event defined in both
  files contributes entries from both. Do not duplicate an entry across them.
- A rule file in `rules/` is loaded into every session. Keep it short; it costs
  input tokens on every request.
- Run `make lint` and `make test` on every change to a script or a skill.
- Record a user-visible change in `README.md`.
