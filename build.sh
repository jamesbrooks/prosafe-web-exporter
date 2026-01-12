#!/bin/bash
set -e

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t jamesbrooks/prosafe-web-exporter:latest \
  --push \
  .
