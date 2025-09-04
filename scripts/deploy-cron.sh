#!/usr/bin/bash

# Scripts adapted from https://www.youtube.com/watch?v=jFrGhodqC08 by Tom Delande
# Licensed under https://creativecommons.org/licenses/by/4.0/

cd /home/matthew/democrasite
flock -n ~/build.lock scripts/deploy.sh >> ~/build.log 2>&1
