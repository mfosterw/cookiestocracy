#!/usr/bin/bash

# Scripts adapted from https://www.youtube.com/watch?v=jFrGhodqC08 by Tom Delande
# Licensed under https://creativecommons.org/licenses/by/4.0/

LOCK_FILE="$(pwd)/build.lock"
cd /home/matthew/democrasite
flock -n $LOCK_FILE scripts/deploy.sh >> build.log 2>&1
