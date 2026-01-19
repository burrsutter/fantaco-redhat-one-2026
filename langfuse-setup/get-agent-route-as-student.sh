#!/bin/bash
# Calculates and exports CHAT_TRACE_URL based on current agentic-userN project
# Usage: source ./get-agent-route-as-student.sh
#
# Exports: CHAT_TRACE_URL
#
# Constructs URL like:
#   https://chatbot-8002-showroom-bwpcf-1-user3.apps.cluster-bwpcf.dynamic.redhatworkshops.io/

# Get current namespace from oc project
NAMESPACE=$(oc project -q 2>/dev/null)

if [ -z "$NAMESPACE" ]; then
    # Try to get namespace from inside a pod
    if [ -f /var/run/secrets/kubernetes.io/serviceaccount/namespace ]; then
        NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
    fi
fi

if [ -z "$NAMESPACE" ]; then
    echo "Error: Could not determine current namespace"
    exit 1
fi

echo "Namespace: $NAMESPACE"

# Extract user from namespace (e.g., agentic-user3 -> user3)
if [[ "$NAMESPACE" =~ ^agentic-(.+)$ ]]; then
    USER="${BASH_REMATCH[1]}"
else
    echo "Error: Namespace '$NAMESPACE' does not match expected pattern agentic-<user>"
    exit 1
fi

# Get cluster ID from existing route (e.g., apps.cluster-bwpcf.dynamic... -> bwpcf)
ROUTE_HOST=$(oc get routes -o jsonpath='{.items[0].spec.host}' 2>/dev/null)

if [ -z "$ROUTE_HOST" ]; then
    echo "Error: No routes found in namespace"
    exit 1
fi

# Try to extract cluster ID from route - handle multiple formats
# Format 1: apps.cluster-XXXX.dynamic.redhatworkshops.io
# Format 2: apps.ocp.XXXX.sandboxNNNN.opentlc.com
CLUSTER_ID=$(echo "$ROUTE_HOST" | sed -n 's/.*\.apps\.cluster-\([^.]*\)\..*/\1/p')

if [ -z "$CLUSTER_ID" ]; then
    # Try Format 2: apps.ocp.XXXX.sandbox...
    CLUSTER_ID=$(echo "$ROUTE_HOST" | sed -n 's/.*\.apps\.ocp\.\([^.]*\)\..*/\1/p')
fi

if [ -z "$CLUSTER_ID" ]; then
    echo "Error: Could not extract cluster ID from route: $ROUTE_HOST"
    exit 1
fi

# Determine the apps domain based on route format
if echo "$ROUTE_HOST" | grep -q "dynamic.redhatworkshops.io"; then
    APPS_DOMAIN="apps.cluster-${CLUSTER_ID}.dynamic.redhatworkshops.io"
    SHOWROOM_NAMESPACE="showroom-${CLUSTER_ID}-1-${USER}"
else
    # opentlc.com format
    SANDBOX_ID=$(echo "$ROUTE_HOST" | sed -n 's/.*\.apps\.ocp\.[^.]*\.\([^.]*\)\.opentlc\.com/\1/p')
    APPS_DOMAIN="apps.ocp.${CLUSTER_ID}.${SANDBOX_ID}.opentlc.com"
    SHOWROOM_NAMESPACE="showroom-${CLUSTER_ID}-1-${USER}"
fi

CHAT_TRACE_URL="https://chatbot-8002-${SHOWROOM_NAMESPACE}.${APPS_DOMAIN}/"

export CHAT_TRACE_URL

echo "CHAT_TRACE_URL=${CHAT_TRACE_URL}"
