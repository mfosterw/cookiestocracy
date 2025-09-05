#!/usr/bin/bash

# Scripts adapted from https://www.youtube.com/watch?v=jFrGhodqC08 by Tom Delande
# Licensed under https://creativecommons.org/licenses/by/4.0/

echo "$(date --utc +%FT%TZ): Fetching remote repository..."
git fetch

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    echo "$(date --utc +%FT%TZ): No changes detected in git"
elif [ $LOCAL = $BASE ]; then
    git pull

    BUILD_VERSION=$(git rev-parse HEAD)
    echo "#(date --utc +%FT%TZ): Releasing new server version. $BUILD_VERSION"

    COMPOSE_FILE="/home/matthew/democrasite/docker-compose.production.yml"
    echo "$(date --utc +%FT%TZ): Running build..."
    docker compose -f $COMPOSE_FILE rm -f
    docker compose -f $COMPOSE_FILE build

    OLD_CONTAINER=$(docker ps -aqf "name=django")
    echo "$(date --utc +%FT%TZ): Scaling server up..."
    BUILD_VERSION=$BUILD_VERSION docker compose -f $COMPOSE_FILE up -d --no-deps --scale django=2 --no-recreate django

    sleep 30

    echo "$(date --utc +%FT%TZ): Scaling old server down..." docker container rm -f $OLD_CONTAINER
    docker compose -f $COMPOSE_FILE up -d --no-deps --scale django=1 --no-recreate django
elif [ $REMOTE = $BASE ]; then
     echo "$(date --utc +%FT%TZ): Local changes detected, you may need to stash"
else
     echo "$(date --utc +%FT%TZ): Git is diverged, this is unexpected."
fi
