# agents

My Claude Code configuration: coding rules, hooks, status line and settings.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/piotrpersona/agents/main/install.sh | bash
```

Piping a script from a URL into `bash` runs whatever that URL happens to serve
at that moment. To read it before it runs:

```sh
curl -fsSL -o install.sh https://raw.githubusercontent.com/piotrpersona/agents/main/install.sh
less install.sh && bash install.sh
```

The installer needs `git` and `jq`. It clones to
`~/developer/github.com/piotrpersona/agents`, then:

- symlinks `rules/*.md` into `~/.claude/rules/`
- symlinks `hooks/*.sh` into `~/.claude/hooks/`
- symlinks each `skills/<name>/` into `~/.claude/skills/`
- symlinks `statusline.sh` to `~/.claude/statusline.sh`
- generates `~/.claude/settings.json` (see below)

Any real file it would replace is moved to `<name>.<timestamp>.bak` first.
Re-running is safe: it pulls, relinks only what changed, and leaves
`settings.json` alone when it already matches.

Override the defaults with env vars:

| Variable | Default |
| --- | --- |
| `AGENTS_DIR` | `~/developer/github.com/piotrpersona/agents` |
| `AGENTS_REPO` | `https://github.com/piotrpersona/agents.git` |
| `CLAUDE_DIR` | `$CLAUDE_CONFIG_DIR`, else `~/.claude` |

Restart Claude Code afterwards to load the new hooks and settings.

## Layout

```
rules/                        auto-loaded by Claude Code in every project
  coding.md                   style, git, Go, Python, OpenRouter
  conversation.md             tone and response shape
  research.md                 ML / data-processing conventions
  go-project-structure.md     hexagonal layout for Go services
hooks/
  codegraph-init-check.sh     SessionStart: flag repos with no CodeGraph index
skills/
  intent-masking/             UUID tokens instead of intent text in MCP calls
statusline.sh                 vendored, see .upstream (MIT)
settings.shared.json          portable settings, tracked here
settings.machine.example.json template for the machine-local overlay
merge.jq                      deep merge: objects recurse, arrays concatenate
.upstream                     origin and pinned commit of vendored files
install.sh
```

Files in `rules/` load automatically in every project, so adding a rule means
adding a file — there is no import list to maintain. `@path` imports in
`CLAUDE.md` take literal paths only; `@dir/*.md` is not supported, which is why
these live in `rules/` instead.

## Settings

Claude Code reads one user-level file, `~/.claude/settings.json`. There is no
user-level `settings.local.json` — that layer exists only per project. So the
split is done at install time rather than by the settings loader:

```
settings.shared.json  +  ~/.claude/settings.machine.json  ->  ~/.claude/settings.json
   (tracked)                  (untracked, per machine)            (generated)
```

`settings.machine.json` holds what cannot travel between machines: the local
caveman proxy `ANTHROPIC_BASE_URL` and the caveman hooks, whose `--adapter`
argument points at an nvm-version-pinned path. It is gitignored. Everything
else — permissions, model, plugins, theme, the rtk and CodeGraph hooks — is
shared.

Arrays concatenate on merge, so a single hook event can take entries from both
files. `PreToolUse` ends up with the rtk hook from shared plus the caveman
hooks from machine.

After editing either file:

```sh
make install   # regenerate settings.json
make diff      # show drift between the live file and repo + overlay
```

## Skills

`skills/intent-masking/` keeps intent text out of MCP tool arguments. Before a
`mcp__*` call with a free-text `intent`, `purpose`, `reason` or `justification`
field, the skill checks the tool schema: if the field is not in `required` it is
dropped, and if it is required `mask_intent.py` mints a UUIDv4 to send instead
of the text.

```sh
mask_intent.py mask --tool <tool> --operation <label>  # mint, or reuse the label's token
mask_intent.py check <value>                           # exit 1 on anything but a UUIDv4
mask_intent.py trail [--operation L] [--all]           # what this session masked
mask_intent.py resolve <intent_id>                     # one record, by token
```

`--operation` makes reuse mechanical: the first call under a label mints a
token and every later call under it returns the same one, so a stateful server
still sees one correlated operation. Labels are scoped to the session, so the
same label in a new session gets a new token.

`trail` is the audit path that needs no UUID in hand — one line per record,
this session by default. The intent text, when recorded, stays in
`~/.claude/intent-masking/ledger.jsonl` (dir `0700`, file `0600`) and never
crosses the wire, so the token is opaque to the server by design. `make test`
runs the skill's tests.

The matching rule in `rules/coding.md` is what makes this fire before the call
rather than after it, since rules load in every session.

## Status line

```
◆ Opus 5  ██░░░░░░░░ 23% 200k   $0.42  󰔟 14m5s  Pro 5h:25% 7d:3%
 main  +156/-23  nvim
```

`statusline.sh` is vendored from
[kcchien/claude-code-statusline](https://github.com/kcchien/claude-code-statusline)
(MIT), pinned at commit `877d2448`. It gives a gradient context bar, cost,
duration, git branch with dirty marker, and the plan rate limits.

`5h` is the current session window and `7d` is the week — the same two numbers
the claude.ai profile and `/usage` show. They turn red above 80%. Both come
from `rate_limits` in the status line payload, which is only present on
claude.ai Pro and Max sign-ins and only after the first API response of a
session, so they are hidden until then and on API-key sign-ins.

The plan name is not in that payload. It comes from `CLAUDE_PLAN` in
`settings.shared.json` (`"Pro"`), which Claude Code passes through to the
status line process. Change it there if the plan changes; the segment is
hidden when the variable is unset. This is the one local change to the
upstream script, marked `LOCAL PATCH` in the file — see `.upstream` for the
pinned commit and how to refresh it.

`CLAUDE_STATUSLINE_NERDFONT=1` is set in `settings.shared.json`, which turns
on the Nerd Font icons and Powerline separators shown above. The terminal font
has to be a [Nerd Font](https://www.nerdfonts.com/) or those glyphs render as
boxes; drop the variable, or set `CLAUDE_STATUSLINE_ASCII=1` for pure ASCII,
if that happens.

## Not tracked here

Transcripts and local state (`projects/`, `sessions/`, `history.jsonl`,
`shell-snapshots/`, `file-history/`, `cache/`) stay out of this repo. They
contain file contents and prompts from private work, and this repo is public.

`CLAUDE.md`, `RTK.md` and `hooks/peon-ping/` are installed and rewritten by
their own tools (rtk, peon-ping), so they are left to those installers.
Third-party skills are managed separately and resolved from `~/.agents` via
`.skill-lock.json`; only skills written here live in `skills/`.
