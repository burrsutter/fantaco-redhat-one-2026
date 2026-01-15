#!/bin/bash
# Creates a Service and Route for port 8002 as cluster admin for ALL users
# Usage: ./create-agent-route-as-admin.sh
#
# This script discovers all showroom namespaces containing "user" in the name
# and creates the necessary Service and Route resources for each.

echo "Discovering all showroom namespaces with 'user' in the name..."

# Find all showroom namespaces with "user" in the name
SHOWROOM_NAMESPACES=$(oc get projects --no-headers 2>/dev/null | grep "showroom.*user" | awk '{print $1}')

if [ -z "$SHOWROOM_NAMESPACES" ]; then
    echo "Error: No showroom namespaces found with 'user' in the name"
    echo "Available showroom projects:"
    oc get projects --no-headers 2>/dev/null | grep "showroom" || echo "  No showroom projects found"
    exit 1
fi

# Count namespaces
NAMESPACE_COUNT=$(echo "$SHOWROOM_NAMESPACES" | wc -l | tr -d ' ')
echo "Found $NAMESPACE_COUNT showroom namespace(s):"
echo "$SHOWROOM_NAMESPACES" | sed 's/^/  /'
echo ""

# Get the cluster's base domain (only need to do this once)
BASE_DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null || true)

if [ -z "$BASE_DOMAIN" ]; then
    # Fallback: try to extract from first namespace pattern (e.g., showroom-m7dw5-1-user1 -> apps.cluster-m7dw5.dynamic.redhatworkshops.io)
    FIRST_NAMESPACE=$(echo "$SHOWROOM_NAMESPACES" | head -1)
    CLUSTER_ID=$(echo "$FIRST_NAMESPACE" | sed -n 's/^showroom-\([^-]*\)-.*/\1/p')
    if [ -n "$CLUSTER_ID" ]; then
        BASE_DOMAIN="apps.cluster-${CLUSTER_ID}.dynamic.redhatworkshops.io"
        echo "Auto-detected base domain: $BASE_DOMAIN"
    fi
fi

if [ -z "$BASE_DOMAIN" ]; then
    echo "Error: Could not determine cluster base domain"
    exit 1
fi

# Track results
SUCCESS_COUNT=0
FAIL_COUNT=0
CREATED_URLS=()

# Loop through each namespace and create Service/Route
for SHOWROOM_NAMESPACE in $SHOWROOM_NAMESPACES; do
    echo "----------------------------------------"
    echo "Processing: $SHOWROOM_NAMESPACE"

    ROUTE_HOST="chatbot-8002-${SHOWROOM_NAMESPACE}.${BASE_DOMAIN}"
    echo "Route will be: https://${ROUTE_HOST}"

    # Create the Service
    if oc apply -n "$SHOWROOM_NAMESPACE" -f - <<EOF
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
    then
        # Create the Route
        if oc apply -n "$SHOWROOM_NAMESPACE" -f - <<EOF
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
        then
            echo "SUCCESS: Created route for $SHOWROOM_NAMESPACE"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            CREATED_URLS+=("https://${ROUTE_HOST}")
        else
            echo "FAILED: Could not create Route for $SHOWROOM_NAMESPACE"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        echo "FAILED: Could not create Service for $SHOWROOM_NAMESPACE"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "========================================"
echo "Summary:"
echo "  Successful: $SUCCESS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo ""

if [ ${#CREATED_URLS[@]} -gt 0 ]; then
    echo "Created URLs:"
    for url in "${CREATED_URLS[@]}"; do
        echo "  $url"
    done
fi
