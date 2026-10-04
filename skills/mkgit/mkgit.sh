#!/usr/bin/env bash
# Start a new repo.
#
#   local (default)  ~/developer/projects/<name>, no remote
#   --remote         same, then moved to ~/developer/<host>/<you>/<name> and
#                    pushed to a new private github repo
#
#   mkgit.sh <name> [--remote] [--dry-run]
set -euo pipefail

DEV_ROOT=${DEV_ROOT:-$HOME/developer}
PROJECTS_DIR=${PROJECTS_DIR:-$DEV_ROOT/projects}

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

name='' remote=0 dry=0
while [ $# -gt 0 ]; do
  case $1 in
    --remote)  remote=1 ;;
    --local)   remote=0 ;;
    --dry-run) dry=1 ;;
    -h|--help) sed -n '2,9p' -- "$0"; exit 0 ;;
    -*)        die "unknown flag: $1" ;;
    *)         [ -z "$name" ] || die "one name at a time"; name=$1 ;;
  esac
  shift
done
[ -n "$name" ] || die "usage: mkgit.sh <name> [--remote]"
case $name in
  */*|.*) die "name must be a plain directory name, got: $name" ;;
esac

dest=$PROJECTS_DIR/$name
final=$dest
if [ "$remote" = 1 ]; then
  command -v gh >/dev/null || die "gh is not installed, so --remote cannot create the repo"
  owner=$(gh api user --jq .login) || die "gh is not logged in"
  final=$DEV_ROOT/github.com/$owner/$name
  [ -e "$final" ] && die "$final already exists"
fi
[ -e "$dest" ] && die "$dest already exists"

if [ "$dry" = 1 ]; then
  printf 'would create %s%s\n' "$final" \
    "$([ "$remote" = 1 ] && printf ' + private github repo %s/%s' "$owner" "$name")"
  exit 0
fi

mkdir -p -- "$dest"
git -C "$dest" init -b main --quiet
printf '.env\n.DS_Store\n' > "$dest/.gitignore"
printf '# %s\n' "$name" > "$dest/README.md"
git -C "$dest" add .gitignore README.md
git -C "$dest" commit -sqm "chore: init $name"

if [ "$remote" = 1 ]; then
  mkdir -p -- "$(dirname -- "$final")"
  mv -- "$dest" "$final"
  gh repo create "$owner/$name" --private --source="$final" --remote=origin --push
fi

printf '%s\n' "$final"
