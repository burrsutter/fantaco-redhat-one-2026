#!/bin/bash
# Source this file to set LANGFLOW_URL and LANGFLOW_API_URL environment variables
# Usage: source 1-view-langflow-urls.sh

export LANGFLOW_URL="https://$(oc get route langflow -o jsonpath='{.spec.host}' 2>/dev/null)"
export LANGFLOW_API_URL="https://$(oc get route langflow-api -o jsonpath='{.spec.host}' 2>/dev/null)"

echo "LANGFLOW_URL=$LANGFLOW_URL"
echo "LANGFLOW_API_URL=$LANGFLOW_API_URL"
