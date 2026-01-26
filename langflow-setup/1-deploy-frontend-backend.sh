#!/bin/bash
# Deploy Langflow frontend and backend API to OpenShift
# Applies both deployments, waits for pods to be ready, and outputs URLs

set -e

echo "Deploying Langflow frontend..."
oc apply -f langflow-openshift.yaml

echo "Deploying Langflow backend API..."
oc apply -f langflow-openshift-with-api.yaml

echo ""
echo "Waiting for frontend pod to be ready..."
oc rollout status deployment/langflow --timeout=600s

echo ""
echo "Waiting for backend API pod to be ready..."
oc rollout status deployment/langflow-api --timeout=600s

echo ""
echo "========================================"
echo "Deployments ready!"
echo "========================================"
echo ""
echo "export LANGFLOW_URL=https://$(oc get route langflow -o jsonpath='{.spec.host}')"
echo "export LANGFLOW_API_URL=https://$(oc get route langflow-api -o jsonpath='{.spec.host}')"
