#!/bin/bash
set -euo pipefail

#constants
URL=http://paffenroth-23.dyn.wpi.edu:9011/api/

cd "$(dirname "$0")"

echo " $(date): checking if server is up"

if curl -sf "$URL" > /dev/null; then
    echo "server is up"
else
    echo "server is down; starting server"
    bash "./deploy_app.sh" > /dev/null 2>&1
    echo "server is back up!"
fi

echo ""

