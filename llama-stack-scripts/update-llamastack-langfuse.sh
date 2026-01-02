#!/bin/bash
# Script to update LlamaStack with Langfuse credentials
# Usage: ./update-llamastack-langfuse.sh <LANGFUSE_SECRET_KEY> <LANGFUSE_PUBLIC_KEY> <LANGFUSE_HOST>
# Example: ./update-llamastack-langfuse.sh "sk-lf-xxx" "pk-lf-xxx" "https://langfuse.example.com"

set -e

# Check arguments
if [ $# -ne 3 ]; then
    echo "Usage: $0 <LANGFUSE_SECRET_KEY> <LANGFUSE_PUBLIC_KEY> <LANGFUSE_HOST>"
    echo "Example: $0 'sk-lf-xxx' 'pk-lf-xxx' 'https://langfuse.example.com'"
    exit 1
fi

LANGFUSE_SECRET_KEY="$1"
LANGFUSE_PUBLIC_KEY="$2"
LANGFUSE_HOST="$3"

echo "Creating/updating langfuse-credentials secret..."
oc create secret generic langfuse-credentials \
    --from-literal=LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
    --from-literal=LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
    --from-literal=LANGFUSE_HOST="$LANGFUSE_HOST" \
    --dry-run=client -o yaml | oc apply -f -

echo "Patching LlamaStackDistribution with Langfuse environment variables..."
oc patch llamastackdistribution llamastack-distribution-vllm --type=json -p '[
  {"op": "add", "path": "/spec/server/containerSpec/env/-", "value": {"name": "LANGFUSE_SECRET_KEY", "valueFrom": {"secretKeyRef": {"name": "langfuse-credentials", "key": "LANGFUSE_SECRET_KEY"}}}},
  {"op": "add", "path": "/spec/server/containerSpec/env/-", "value": {"name": "LANGFUSE_PUBLIC_KEY", "valueFrom": {"secretKeyRef": {"name": "langfuse-credentials", "key": "LANGFUSE_PUBLIC_KEY"}}}},
  {"op": "add", "path": "/spec/server/containerSpec/env/-", "value": {"name": "LANGFUSE_HOST", "valueFrom": {"secretKeyRef": {"name": "langfuse-credentials", "key": "LANGFUSE_HOST"}}}}
]'

echo "Done! Langfuse credentials have been configured for LlamaStack."
echo "The LlamaStack operator will reconcile and restart the pod automatically."
