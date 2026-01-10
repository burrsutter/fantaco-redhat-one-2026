#!/bin/bash
# Calculates and exports CHAT_TRACE_URL based on current oc project
# Usage: source ./get-agent-route-as-student.sh
#
# Exports: CHAT_TRACE_URL

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

# Extract cluster ID from namespace pattern
# e.g., showroom-s5kx7-1-user1 -> s5kx7
#       agentic-user1 -> need to find showroom namespace
if [[ "$NAMESPACE" =~ ^showroom-([^-]+)-.* ]]; then
    CLUSTER_ID="${BASH_REMATCH[1]}"
    SHOWROOM_NAMESPACE="$NAMESPACE"
elif [[ "$NAMESPACE" =~ ^agentic-(.+)$ ]]; then
    USER="${BASH_REMATCH[1]}"
    # Try to find showroom namespace for this user
    SHOWROOM_NAMESPACE=$(oc get projects --no-headers 2>/dev/null | grep "showroom.*${USER}" | awk '{print $1}' | head -1)
    if [ -z "$SHOWROOM_NAMESPACE" ]; then
        echo "Error: Could not find showroom namespace for $USER"
        exit 1
    fi
    CLUSTER_ID=$(echo "$SHOWROOM_NAMESPACE" | sed -n 's/^showroom-\([^-]*\)-.*/\1/p')
else
    echo "Error: Namespace '$NAMESPACE' does not match expected pattern"
    echo "Expected: showroom-<cluster>-<n>-<user> or agentic-<user>"
    exit 1
fi

if [ -z "$CLUSTER_ID" ]; then
    echo "Error: Could not extract cluster ID from namespace"
    exit 1
fi

BASE_DOMAIN="apps.cluster-${CLUSTER_ID}.dynamic.redhatworkshops.io"
CHAT_TRACE_URL="https://chatbot-8002-${SHOWROOM_NAMESPACE}.${BASE_DOMAIN}"

export CHAT_TRACE_URL

echo "CHAT_TRACE_URL=${CHAT_TRACE_URL}"
