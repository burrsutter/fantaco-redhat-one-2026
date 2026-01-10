#!/bin/bash
# Creates the Langfuse Route and exports LANGFUSE_HOST and LANGFUSE_URL
# Usage: source ./create-langfuse-url.sh

# Get current namespace from oc project
NAMESPACE=$(oc project -q)
if [ -z "$NAMESPACE" ]; then
    echo "Error: Could not determine current namespace" >&2
    echo "Make sure you are logged in and have a project selected" >&2
    exit 1
fi

echo "Using namespace: $NAMESPACE"

# Get the cluster's base domain
BASE_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null)

if [ -z "$BASE_DOMAIN" ]; then
    # Fallback: try to get from existing routes in namespace
    BASE_DOMAIN=$(oc get routes -n "$NAMESPACE" -o jsonpath='{.items[0].spec.host}' 2>/dev/null | sed 's/^[^.]*\.//')
fi

if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain" >&2
    exit 1
fi

# Construct the Langfuse URL
LANGFUSE_HOST="langfuse-${NAMESPACE}.${BASE_DOMAIN}"
LANGFUSE_URL="https://${LANGFUSE_HOST}"

echo "Creating Langfuse Route..."
echo "Host will be: $LANGFUSE_URL"

# Create the Route (points to langfuse-web Service that Helm will create)
oc apply -n "$NAMESPACE" -f - <<EOF
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: langfuse
spec:
  host: ${LANGFUSE_HOST}
  port:
    targetPort: 3000
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  to:
    kind: Service
    name: langfuse-web
    weight: 100
EOF

echo ""
echo "Route created:"
oc get route langfuse -n "$NAMESPACE"
echo ""

# If sourced, export the variables; if executed, print them
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced
    export LANGFUSE_HOST
    export LANGFUSE_URL
    echo "Exported LANGFUSE_HOST=${LANGFUSE_HOST}"
    echo "Exported LANGFUSE_URL=${LANGFUSE_URL}"
else
    # Script is being executed
    echo "LANGFUSE_HOST=${LANGFUSE_HOST}"
    echo "LANGFUSE_URL=${LANGFUSE_URL}"
fi
