#!/usr/bin/env bash
# Post-deploy smoke test. Exits non-zero on the first failure.
set -euo pipefail
BASE="${1:-http://localhost:8000}"

echo "Waiting for $BASE/ready ..."
for i in $(seq 1 30); do
  if curl -fsS "$BASE/ready" >/dev/null 2>&1; then break; fi
  [ "$i" -eq 30 ] && { echo "FAIL: service never became ready"; exit 1; }
  sleep 2
done

curl -fsS "$BASE/health" >/dev/null && echo "ok: /health"
curl -fsS -X POST "$BASE/items" -H 'Content-Type: application/json' \
  -d '{"name":"smoke-test"}' >/dev/null && echo "ok: POST /items"
curl -fsS "$BASE/items" | grep -q "smoke-test" && echo "ok: GET /items"
curl -fsS "$BASE/metrics" | grep -q http_requests_total && echo "ok: /metrics"
echo "SMOKE TEST PASSED"
