#!/bin/bash
# Creates a Service and Route for port 8002 from inside a showroom pod
# Usage: ./create-route.sh [showroom-name]
# Example: ./create-route.sh showroom-97v4s-1-user2
#
# If no showroom name is provided, it will use the current namespace

set -e

# Get showroom name from argument or current namespace
if [ -n "$1" ]; then
    SHOWROOM_NAME="$1"
else
    # Try to get namespace from inside the pod
    if [ -f /var/run/secrets/kubernetes.io/serviceaccount/namespace ]; then
        SHOWROOM_NAME=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
    else
        # Fallback to oc project
        SHOWROOM_NAME=$(oc project -q 2>/dev/null)
    fi
fi

if [ -z "$SHOWROOM_NAME" ]; then
    echo "Error: Could not determine showroom name"
    echo "Usage: $0 <showroom-name>"
    echo "Example: $0 showroom-97v4s-1-user2"
    exit 1
fi

echo "Using showroom/namespace: $SHOWROOM_NAME"

# Get the cluster's base domain
BASE_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null)

if [ -z "$BASE_DOMAIN" ]; then
    # Fallback: try to get from existing routes
    BASE_DOMAIN=$(oc get routes -n "$SHOWROOM_NAME" -o jsonpath='{.items[0].spec.host}' 2>/dev/null | sed 's/^[^.]*\.//')
fi

if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain"
    exit 1
fi

ROUTE_HOST="chatbot-8002-${SHOWROOM_NAME}.${BASE_DOMAIN}"

echo "Creating Service and Route..."
echo "Route will be: https://${ROUTE_HOST}"

# Create the Service
oc apply -n "$SHOWROOM_NAME" -f - <<EOF
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
oc apply -n "$SHOWROOM_NAME" -f - <<EOF
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

echo ""
echo "Done! Access your chatbot at:"
echo "https://${ROUTE_HOST}"
echo ""
echo "Test with: curl https://${ROUTE_HOST}/health"
