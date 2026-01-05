#!/bin/bash

# Check remote application logs for debug output

echo "Connecting to remote server and checking logs..."

ssh -o StrictHostKeyChecking=no nathan@vit-dev-website << 'ENDSSH'
cd /home/nathan/vitruvian-developer
echo 'Serbatik11!!' | sudo -S docker logs primary-assistant-web 2>&1 | grep -A 10 -B 5 'GeminiService\|GEMINI_API_KEY\|quota_manager' | tail -50
ENDSSH
