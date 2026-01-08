#!/bin/bash

# Usage: ./create-workbench-8002-route.sh [user]
# Example: ./create-workbench-8002-route.sh user1
#          ./create-workbench-8002-route.sh user2

USER="${1:-user1}"
NAMESPACE="agentic-${USER}"

# Verify namespace exists
if ! oc get namespace "$NAMESPACE" &>/dev/null; then
    echo "Error: Namespace $NAMESPACE does not exist"
    echo "Usage: $0 [user]  (e.g., user1, user2, user3)"
    exit 1
fi
echo "Using namespace: $NAMESPACE"
echo "Target user: $USER"

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

# Create NetworkPolicy to allow ingress on port 8002
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-workbench-8002
spec:
  podSelector:
    matchLabels:
      app: ${USER}-workbench
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          network.openshift.io/policy-group: ingress
    ports:
    - port: 8002
      protocol: TCP
  policyTypes:
  - Ingress
EOF

# Create Service targeting the workbench pod
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: workbench-8002
spec:
  selector:
    app: ${USER}-workbench
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
