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
API_URL="http://localhost:3000/api/chat/chat"
USER_ACCESS_TOKEN=$(poetry run python -m scripts.print_access_token)

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" \
  --no-buffer \
  -d "{\"message\": \"${MESSAGE}\", \"thread_id\": \"${THREAD_ID}\", \"domain_id\": \"b54feb10-5011-429e-8585-35913d797d8e\" }" \
  "${API_URL}"
