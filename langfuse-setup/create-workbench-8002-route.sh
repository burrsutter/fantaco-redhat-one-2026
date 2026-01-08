#!/bin/bash

# Find namespace starting with "agentic-" or use current namespace
NAMESPACE=$(oc get namespaces -o name | grep "agentic-" | head -1 | sed 's|namespace/||')
if [ -z "$NAMESPACE" ]; then
    NAMESPACE=$(oc project -q)
fi
echo "Using namespace: $NAMESPACE"

# Get the cluster's base domain from any existing route
BASE_DOMAIN=$(oc get routes -A -o jsonpath='{.items[0].spec.host}' 2>/dev/null | sed 's/^[^.]*\.//')
if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain"
    exit 1
fi

# Construct new host for workbench-8002
NEW_HOST="workbench-8002-${NAMESPACE}.${BASE_DOMAIN}"

echo "Creating Service and Route for port 8002..."
echo "Host will be: https://${NEW_HOST}"

# Create Service targeting the workbench pod
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: workbench-8002
spec:
  selector:
    app: user1-workbench
  ports:
    - port: 8002
      targetPort: 8002
      protocol: TCP
EOF

# Create Route with explicit host
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: workbench-8002
spec:
  host: ${NEW_HOST}
  port:
    targetPort: 8002
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  to:
    kind: Service
    name: workbench-8002
    weight: 100
EOF

# Verify
echo ""
echo "Route created:"
oc get route workbench-8002 -n "$NAMESPACE"
