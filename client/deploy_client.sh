#!/bin/bash
# Deployment script
# Usage:
#   ./deploy_client.sh dev   → deploys to client.fleminganalytic.com (development)
#   ./deploy_client.sh prod  → deploys to fleminganalytic.com (production)

REMOTE_SERVER="fleminganalytic.com"
LOCAL_ZIP="frontend_dist_FINAL.zip"
TARGET=${1:-dev}

if [ "$TARGET" = "prod" ]; then
  REMOTE_PATH="/var/www/fleminganalytic/client-prod"
  LABEL="fleminganalytic.com (PRODUCTION)"
else
  REMOTE_PATH="/var/www/fleminganalytic/client"
  LABEL="client.fleminganalytic.com (development)"
fi

echo "Deploying to $LABEL..."

echo "Step 1: Uploading $LOCAL_ZIP to server..."
scp $LOCAL_ZIP root@$REMOTE_SERVER:/tmp/

echo "Step 2: Deploying on server..."
ssh root@$REMOTE_SERVER "
  mkdir -p $REMOTE_PATH
  unzip -o /tmp/frontend_dist_FINAL.zip -d /tmp/frontend_unpack
  cp -r /tmp/frontend_unpack/dist/* $REMOTE_PATH/
  chown -R www-data:www-data $REMOTE_PATH
  rm -rf /tmp/frontend_unpack /tmp/frontend_dist_FINAL.zip
  echo 'Deployment to $REMOTE_PATH complete!'
"
