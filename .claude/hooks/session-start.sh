#!/usr/bin/env bash
# Pull --rebase at session start so PC <-> laptop work doesn't diverge.
# Bails safely on: no commits, detached HEAD, no remote, no upstream, mid-operation.
set -u

cd "$(dirname "$0")/../.." || exit 0

if ! git rev-parse HEAD >/dev/null 2>&1; then exit 0; fi
if ! git symbolic-ref -q HEAD >/dev/null; then exit 0; fi

git_dir=$(git rev-parse --git-dir 2>/dev/null) || exit 0
for f in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply; do
  if [ -e "$git_dir/$f" ]; then exit 0; fi
done

git remote get-url origin >/dev/null 2>&1 || exit 0
git rev-parse --verify "@{u}" >/dev/null 2>&1 || exit 0

branch=$(git symbolic-ref --short HEAD)
if git pull --rebase --autostash >/dev/null 2>&1; then
  printf '{"systemMessage":"superopt: synced from origin/%s"}\n' "$branch"
else
  git rebase --abort >/dev/null 2>&1 || true
  echo '{"systemMessage":"superopt: pull failed at startup, may have diverged"}'
fi

exit 0
