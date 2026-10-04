---
name: mkgit
description: Start a new repo - local throwaway in ~/developer/projects/<name>,
  or with --remote a private github repo under ~/developer/github.com/<you>/<name>.
  Use for /mkgit, "new project", "scratch repo", or "start a repo for this".
---

# mkgit

```sh
~/.claude/skills/mkgit/mkgit.sh <name> [--remote] [--dry-run]
```

- default: `~/developer/projects/<name>`, `git init -b main`, `.gitignore`
  (`.env`, `.DS_Store`), `README.md`, one signed `chore: init <name>` commit,
  no remote.
- `--remote`: the same, then moved to `~/developer/github.com/<you>/<name>` and
  pushed to a **new private** github repo.

Local is the default. Only pass `--remote` when the user asks for a remote,
since it creates something on github under their account.

The name must be a plain directory name. The script refuses to touch an
existing directory, and prints the final path - `cd` there before writing any
project files, and add the real `.gitignore` entries for whatever language the
project turns out to be.
