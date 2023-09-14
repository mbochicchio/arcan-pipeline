#!/bin/bash

docker build --tag arcan/arcan-benchmark:snapshot .

docker run --env-file .env --rm -it -v .:/data \
    arcan/arcan-benchmark:snapshot /data/$1 $2
