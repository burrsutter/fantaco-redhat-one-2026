#!/bin/bash
# Creates a Service and Route for port 8002 as cluster admin
# Usage: ./create-agent-route-as-admin.sh <user>
# Example: ./create-agent-route-as-admin.sh user1
#
# This script discovers the showroom namespace for the given user
# and creates the necessary Service and Route resources.

set -e

if [ -z "$1" ]; then
    echo "Error: User argument required"
    echo "Usage: $0 <user>"
    echo "Example: $0 user1"
    exit 1
fi

USER="$1"

echo "Looking for showroom namespace for: $USER"

# Discover the showroom namespace for this user
SHOWROOM_NAMESPACE=$(oc get projects --no-headers 2>/dev/null | grep "showroom.*${USER}" | awk '{print $1}' | head -1)

if [ -z "$SHOWROOM_NAMESPACE" ]; then
    echo "Error: Could not find showroom namespace for $USER"
    echo "Available showroom projects:"
    oc get projects --no-headers 2>/dev/null | grep "showroom" || echo "  No showroom projects found"
    exit 1
fi

echo "Found namespace: $SHOWROOM_NAMESPACE"

# Get the cluster's base domain
BASE_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null || true)

if [ -z "$BASE_DOMAIN" ]; then
    # Fallback: try to extract from namespace pattern (e.g., showroom-m7dw5-1-user1 -> apps.cluster-m7dw5.dynamic.redhatworkshops.io)
    CLUSTER_ID=$(echo "$SHOWROOM_NAMESPACE" | sed -n 's/^showroom-\([^-]*\)-.*/\1/p')
    if [ -n "$CLUSTER_ID" ]; then
        BASE_DOMAIN="apps.cluster-${CLUSTER_ID}.dynamic.redhatworkshops.io"
        echo "Auto-detected base domain: $BASE_DOMAIN"
    fi
fi

if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain"
    exit 1
fi

ROUTE_HOST="chatbot-8002-${SHOWROOM_NAMESPACE}.${BASE_DOMAIN}"

echo "Creating Service and Route..."
echo "Route will be: https://${ROUTE_HOST}"

# Create the Service
oc apply -n "$SHOWROOM_NAMESPACE" -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: chatbot-8002
spec:
  selector:
    app.kubernetes.io/name: showroom
  ports:
    - port: 8002
      targetPort: 8002
      protocol: TCP
EOF

# Create the Route
oc apply -n "$SHOWROOM_NAMESPACE" -f - <<EOF
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: chatbot-8002
spec:
  host: ${ROUTE_HOST}
  port:
    targetPort: 8002
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  to:
    kind: Service
    name: chatbot-8002
    weight: 100
EOF

CHAT_TRACE_URL="https://${ROUTE_HOST}"

echo ""
echo "Done! Access the chatbot at:"
echo "${CHAT_TRACE_URL}"
echo ""
echo "Test with: curl ${CHAT_TRACE_URL}/health"
