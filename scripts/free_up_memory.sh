#!/usr/bin/env bash

echo "Bringing down docker-compose..."
docker-compose down

echo "Removing all docker containers that have exited"
docker container rm -f $(docker ps --filter "status=exited" --quiet)
