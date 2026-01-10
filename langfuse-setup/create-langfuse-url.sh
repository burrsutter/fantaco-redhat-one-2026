#!/bin/bash
# Get the Langfuse URL for the current namespace
# Usage: source ./get-langfuse-url.sh
#   or:  export LANGFUSE_URL=$(./get-langfuse-url.sh)

# Get current namespace from oc project
NAMESPACE=$(oc project -q)
if [ -z "$NAMESPACE" ]; then
    echo "Error: Could not determine current namespace" >&2
    echo "Make sure you are logged in and have a project selected" >&2
    exit 1
fi

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
LANGFUSE_URL="https://langfuse-${NAMESPACE}.${BASE_DOMAIN}"

# If sourced, export the variable; if executed, print the URL
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced
    export LANGFUSE_URL
    echo "Exported LANGFUSE_URL=${LANGFUSE_URL}"
else
    # Script is being executed
    echo "$LANGFUSE_URL"
fi
