#!/usr/bin/env bash
# Auto-sync at end of Claude Code session.
# Commits any pending work as a "wip:" checkpoint, pulls --rebase, pushes.
# Bails safely on: no commits yet, detached HEAD, mid-operation, push/pull failure.
set -u

cd "$(dirname "$0")/../.." || exit 0

# Bail if no commits yet (the user makes the first commit themselves)
if ! git rev-parse HEAD >/dev/null 2>&1; then
  echo '{"systemMessage":"superopt: no commits yet, skipping auto-sync"}'
  exit 0
fi

if ! git symbolic-ref -q HEAD >/dev/null; then
  echo '{"systemMessage":"superopt: detached HEAD, skipping auto-sync"}'
  exit 0
fi

git_dir=$(git rev-parse --git-dir 2>/dev/null) || exit 0
for f in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply; do
  if [ -e "$git_dir/$f" ]; then
    echo '{"systemMessage":"superopt: git operation in progress, skipping auto-sync"}'
    exit 0
  fi
done

branch=$(git symbolic-ref --short HEAD)

# Commit pending changes as a wip checkpoint
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  git add -A
  ts=$(date -u +"%Y-%m-%dT%H:%MZ")
  git commit -m "wip: auto-sync $ts" --no-verify >/dev/null 2>&1 || true
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo '{"systemMessage":"superopt: no origin remote, skipping push"}'
  exit 0
fi

# Pull --rebase if upstream exists
if git rev-parse --verify "@{u}" >/dev/null 2>&1; then
  if ! git pull --rebase --autostash >/dev/null 2>&1; then
    git rebase --abort >/dev/null 2>&1 || true
    echo '{"systemMessage":"superopt auto-sync: pull conflicted, resolve manually next session"}'
    exit 0
  fi
fi

# Push (sets upstream on first push)
if git push -u origin "$branch" >/dev/null 2>&1; then
  printf '{"systemMessage":"superopt auto-sync: pushed to origin/%s"}\n' "$branch"
else
  echo '{"systemMessage":"superopt auto-sync: push failed (auth or network?)"}'
fi

exit 0
