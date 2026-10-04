---
name: gitclone
description: Clone a repo into its place in the workspace - public github repos
  into ~/developer/github.com/<org>/<repo>, private and work repos into
  ~/work/<org>/<repo>. Use for /gitclone, "clone this repo", or any `git clone`
  of a repo that is not yet on this machine.
---

# gitclone

Never run `git clone` straight into the current directory. The path is decided
by who owns the repo, so run the script and let it place the clone.

```sh
~/.claude/skills/gitclone/clone.sh <owner/repo|clone-url> [--dev|--work] [--dry-run]
```

- public github repo -> `~/developer/github.com/<org>/<repo>`
- private github repo -> `~/work/<org>/<repo>`

Visibility comes from `gh repo view --json isPrivate`, so github.com needs no
flag. Any other host, or no `gh`, needs `--dev` or `--work` - ask which one
rather than guessing. Pass the flag as well when the user says where it goes
("clone it into work"), since an explicit flag skips the lookup.

The script is idempotent: an existing clone at the target is reported and left
alone. It prints the path it used - `cd` there afterwards and say where it
landed.
