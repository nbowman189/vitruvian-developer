#!/bin/bash
cd /home/nathan/vitruvian-developer
docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs --tail=300 web | grep -A 30 -B 5 "behavior"
