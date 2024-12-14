#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <thread_id> <message>"
  echo "Example: $0 new \"Hello, how can you help me?\""
  exit 1
fi

if [ -z "$2" ]; then
  echo "Message is required"
  exit 1
fi

THREAD_ID=$1
MESSAGE=$2
API_URL="http://localhost:8399/chat/${THREAD_ID}"
USER_ACCESS_TOKEN=$(poetry run python -m scripts.print_access_token)

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" \
  --no-buffer \
  -d "{\"message\": \"${MESSAGE}\"}" \
  "${API_URL}"
