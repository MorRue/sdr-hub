#!/bin/bash
# Bring down any existing containers (remove old ones)
docker compose down

# Bring them up again, recreating containers
docker compose up -d --force-recreate
