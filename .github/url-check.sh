#!/bin/sh
# Check all STEX URLs contained in files that have been modified since a commit.
set -e
if [ "$#" -ne 2 ]; then
    echo "Pass the commit/branch to compare to as first argument, the src folder as second."
    exit 1
fi

BASE="$(git merge-base @ "$1")"

git diff "$BASE" --name-only -- "$2" | xargs --delimiter '\n' python .github/st-check-updates.py --mode=id
