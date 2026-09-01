#!/bin/bash
# ==============================================================================
# R-DIOS Application Health Smoke Test
# Hits the core API health endpoints after deployment to ensure components are up.
# Usage: ./health-check.sh <api_url>
# Example: ./health-check.sh https://api.rdios.petpooja.com
# ==============================================================================

API_URL=${1:-http://localhost:8000}
MAX_RETRIES=5
RETRY_INTERVAL=10

echo "Running Health Checks against: $API_URL"

for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempt $i/$MAX_RETRIES..."
    
    # Check basic health endpoint
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
    
    if [ "$HTTP_STATUS" == "200" ]; then
        echo "✅ Primary API Health Check Passed! (200 OK)"
        
        # Optionally query the /health/detailed endpoint to ensure Database/Redis are alive
        echo "Validating detailed service connections..."
        DETAILED_JSON=$(curl -s "$API_URL/health/detailed")
        
        if echo "$DETAILED_JSON" | grep -q '"status":"healthy"'; then
            echo "✅ Detailed Services (Postgres / Redis) Check Passed!"
            exit 0
        else
            echo "⚠️  API is up, but a dependent service may be degraded: $DETAILED_JSON"
            exit 0 # We pass the smoke test, but raise a warning
        fi
    fi
    
    echo "❌ Health check failed resulting in HTTP $HTTP_STATUS. Retrying in $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
done

echo "🚨 FATAL: Application did not become healthy within the timeout period!"
exit 1
