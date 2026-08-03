#!/usr/bin/env bash
# Create a test user for local development, if one doesn't already exist.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
TEST_EMAIL="${TEST_EMAIL:-dev@enginex.ai}"
TEST_PASSWORD="${TEST_PASSWORD:-DevPassword1}"
TEST_NAME="${TEST_NAME:-Dev User}"

response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"name\":\"$TEST_NAME\"}")

if [ "$response" = "201" ]; then
  echo "Created test user: $TEST_EMAIL / $TEST_PASSWORD"
elif [ "$response" = "409" ]; then
  echo "Test user already exists: $TEST_EMAIL"
else
  echo "Unexpected response ($response) while seeding test user" >&2
  exit 1
fi
