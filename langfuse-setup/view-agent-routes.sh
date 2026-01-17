#!/bin/bash
# Lists all chatbot-8002 routes created by create-agent-route-as-admin.sh
# Usage: ./view-agent-routes.sh
#
# Shows the status of chatbot-8002 routes across all showroom-*-user* namespaces

echo "Checking for chatbot-8002 routes in showroom namespaces..."
echo ""

# Find all showroom namespaces with "user" in the name
SHOWROOM_NAMESPACES=$(oc get projects --no-headers 2>/dev/null | grep "showroom.*user" | awk '{print $1}')

if [ -z "$SHOWROOM_NAMESPACES" ]; then
    echo "No showroom namespaces found with 'user' in the name"
    exit 1
fi

NAMESPACE_COUNT=$(echo "$SHOWROOM_NAMESPACES" | wc -l | tr -d ' ')
FOUND_COUNT=0
MISSING_COUNT=0

printf "%-35s %-10s %s\n" "NAMESPACE" "STATUS" "URL"
printf "%-35s %-10s %s\n" "---------" "------" "---"

for ns in $SHOWROOM_NAMESPACES; do
    ROUTE_HOST=$(oc get route chatbot-8002 -n "$ns" -o jsonpath='{.spec.host}' 2>/dev/null)

    if [ -n "$ROUTE_HOST" ]; then
        printf "%-35s %-10s %s\n" "$ns" "OK" "https://${ROUTE_HOST}"
        FOUND_COUNT=$((FOUND_COUNT + 1))
    else
        printf "%-35s %-10s %s\n" "$ns" "MISSING" "-"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

echo ""
echo "========================================"
echo "Summary:"
echo "  Total namespaces: $NAMESPACE_COUNT"
echo "  Routes found:     $FOUND_COUNT"
echo "  Routes missing:   $MISSING_COUNT"

if [ "$MISSING_COUNT" -eq 0 ]; then
    echo ""
    echo "All routes are configured."
else
    echo ""
    echo "Run ./create-agent-route-as-admin.sh to create missing routes."
fi
