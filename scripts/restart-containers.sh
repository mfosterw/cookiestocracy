#!/usr/bin/bash

COMPOSE_FILE="/home/matthew/democrasite/docker-compose.production.yml"
OLD_CONTAINER=$(docker ps -aq)
echo "$(date --utc +%FT%TZ): Scaling servers up..."
BUILD_VERSION=$BUILD_VERSION docker compose -f $COMPOSE_FILE up -d --no-deps --scale django=2 --scale postgres=2 --scale celeryworker=2 --scale celerybeat=2 --scale flower=2 --scale nginx=2 --no-recreate

sleep 30

echo "$(date --utc +%FT%TZ): Scaling old server down..."
docker container rm -f $OLD_CONTAINER
docker compose up -d --no-deps traefik  # easier than excluding from delete and allows cycling traefik with <2 seconds down
docker compose -f $COMPOSE_FILE up -d --no-deps --scale django=1 --scale postgres=1 --scale celeryworker=1 --scale celerybeat=1 --scale flower=1 --scale nginx=1 --no-recreate
