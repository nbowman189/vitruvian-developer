#!/bin/bash
# Fetch recent application logs from remote server

ssh nathan@vit-dev-website << 'ENDSSH'
cd /home/nathan/vitruvian-developer
sudo docker logs primary-assistant-web 2>&1 | tail -100
ENDSSH
