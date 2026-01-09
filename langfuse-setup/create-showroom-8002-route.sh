#!/bin/bash

# Uses the current oc project to create a route for port 8002
# No arguments needed - derives namespace and user from current context

# Get current namespace from oc project
NAMESPACE=$(oc project -q)
if [ -z "$NAMESPACE" ]; then
    echo "Error: Could not determine current namespace"
    echo "Make sure you are logged in and have a project selected"
    exit 1
fi

# Extract user from namespace (assumes format: agentic-userX)
if [[ "$NAMESPACE" =~ ^agentic-(.+)$ ]]; then
    USER="${BASH_REMATCH[1]}"
else
    echo "Error: Namespace '$NAMESPACE' does not match expected pattern 'agentic-*'"
    exit 1
fi

echo "Using namespace: $NAMESPACE"
echo "Detected user: $USER"

# Get the cluster's base domain - try multiple methods
# Method 1: From ingress config (most reliable)
BASE_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null)

# Method 2: From routes in current namespace
if [ -z "$BASE_DOMAIN" ]; then
    BASE_DOMAIN=$(oc get routes -n "$NAMESPACE" -o jsonpath='{.items[0].spec.host}' 2>/dev/null | sed 's/^[^.]*\.//')
fi

# Method 3: From console route (if accessible)
if [ -z "$BASE_DOMAIN" ]; then
    BASE_DOMAIN=$(oc get route console -n openshift-console -o jsonpath='{.spec.host}' 2>/dev/null | sed 's/^console\.//')
fi

if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain"
    echo "Try running: oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}'"
    exit 1
fi

# Construct new host for showroom-8002
NEW_HOST="showroom-8002-${NAMESPACE}.${BASE_DOMAIN}"

echo "Creating Service and Route for port 8002..."
echo "Host will be: https://${NEW_HOST}"

# Create NetworkPolicy to allow ingress on port 8002
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-showroom-8002
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
  name: showroom-8002
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
  name: showroom-8002
spec:
  host: ${NEW_HOST}
  port:
    targetPort: 8002
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  to:
    kind: Service
    name: showroom-8002
    weight: 100
EOF

# Verify
echo ""
echo "Route created:"
oc get route showroom-8002 -n "$NAMESPACE"
echo ""
echo "Access your application at: https://${NEW_HOST}"
