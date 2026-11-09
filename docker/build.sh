#!/bin/bash
set -e
VERSION="$(cat backend/VERSION | tr -d '[:space:]')"
docker build -f docker/nginx.Dockerfile -t raveberry/raveberry-nginx:$VERSION -t raveberry/raveberry-nginx .
docker build -f docker/Dockerfile -t raveberry/raveberry:$VERSION -t raveberry/raveberry .
echo "Publish using:"
echo "docker push raveberry/raveberry-nginx"
echo "docker push raveberry/raveberry"
