#!/usr/bin/bash

# Scripts adapted from https://www.youtube.com/watch?v=jFrGhodqC08 by Tom Delande
# Licensed under https://creativecommons.org/licenses/by/4.0/

git fetch

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ "$LOCAL" = "$REMOTE" ]; then
    true
    # echo "$(date --utc +%FT%TZ): No changes detected in git"
elif [ "$LOCAL" = "$BASE" ]; then
    git pull
    scripts/deploy.sh
elif [ "$REMOTE" = "$BASE" ]; then
     echo "$(date --utc +%FT%TZ): Local changes detected, you may need to stash"
else
     echo "$(date --utc +%FT%TZ): Git is diverged, this is unexpected."
fi
