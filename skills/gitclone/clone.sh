#!/usr/bin/env bash
# Clone a repo into its place in the workspace:
#
#   public github repo   -> ~/developer/github.com/<org>/<repo>
#   private or work repo -> ~/work/<org>/<repo>
#
# Visibility decides the target, so it needs `gh` for github.com. Any other
# host, or no gh, needs --dev or --work.
#
#   clone.sh <repo|url> [--dev|--work] [--dry-run]
set -euo pipefail

DEV_ROOT=${DEV_ROOT:-$HOME/developer}
WORK_ROOT=${WORK_ROOT:-$HOME/work}

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

target='' dry=0 arg=''
while [ $# -gt 0 ]; do
  case $1 in
    --dev)     target=dev ;;
    --work)    target=work ;;
    --dry-run) dry=1 ;;
    -h|--help) sed -n '2,11p' -- "$0"; exit 0 ;;
    -*)        die "unknown flag: $1" ;;
    *)         [ -z "$arg" ] || die "one repo at a time"; arg=$1 ;;
  esac
  shift
done
[ -n "$arg" ] || die "usage: clone.sh <repo|url> [--dev|--work]"

# host/org/repo out of either a URL (https, ssh, scp-like) or owner/repo
case $arg in
  *://*)     rest=${arg#*://}; rest=${rest#*@} ;;
  *@*:*)     rest=${arg#*@}; rest=${rest/://} ;;
  */*/*)     rest=$arg ;;
  */*)       rest=github.com/$arg ;;
  *)         die "need owner/repo or a clone URL, got: $arg" ;;
esac
rest=${rest%.git}; rest=${rest%/}
host=${rest%%/*}; path=${rest#*/}
org=${path%%/*}; repo=${path##*/}
[ "$org" != "$path" ] && [ -n "$org" ] && [ -n "$repo" ] || die "cannot read owner/repo from: $arg"

if [ -z "$target" ]; then
  [ "$host" = github.com ] || die "$host is not github.com; pass --dev or --work"
  command -v gh >/dev/null || die "gh is not installed; pass --dev or --work"
  private=$(gh repo view "$org/$repo" --json isPrivate --jq .isPrivate) \
    || die "cannot read $org/$repo with gh; pass --dev or --work"
  [ "$private" = true ] && target=work || target=dev
fi

case $target in
  work) dest=$WORK_ROOT/$org/$repo ;;
  dev)  dest=$DEV_ROOT/$host/$org/$repo ;;
esac

if [ -d "$dest/.git" ]; then
  printf 'already cloned: %s\n' "$dest"
  exit 0
fi
[ -e "$dest" ] && die "$dest exists and is not a git repo"

if [ "$dry" = 1 ]; then
  printf 'would clone %s/%s (%s) -> %s\n' "$org" "$repo" "$target" "$dest"
  exit 0
fi

mkdir -p -- "$(dirname -- "$dest")"
if [ "$host" = github.com ] && command -v gh >/dev/null; then
  gh repo clone "$org/$repo" "$dest"
else
  git clone "$arg" "$dest"
fi
printf '%s\n' "$dest"
