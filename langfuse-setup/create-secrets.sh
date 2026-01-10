#!/bin/bash
# Generate and export secrets for Langfuse deployment
# Usage: source ./create-secrets.sh
#
# This script generates random secrets needed for Langfuse Helm installation

# Generate random secrets
export LF_SALT="$(openssl rand -hex 16)"
export LF_NEXTAUTH_SECRET="$(openssl rand -hex 32)"
export PG_PASS="$(openssl rand -hex 16)"
export CH_PASS="$(openssl rand -hex 16)"
export REDIS_PASS="$(openssl rand -hex 16)"
export S3_ROOT_PASS="$(openssl rand -hex 16)"

echo "Generated secrets:"
echo "  LF_SALT=${LF_SALT}"
echo "  LF_NEXTAUTH_SECRET=${LF_NEXTAUTH_SECRET}"
echo "  PG_PASS=${PG_PASS}"
echo "  CH_PASS=${CH_PASS}"
echo "  REDIS_PASS=${REDIS_PASS}"
echo "  S3_ROOT_PASS=${S3_ROOT_PASS}"
echo ""

echo "Creating Kubernetes secrets..."

oc create secret generic langfuse-general \
  --from-literal=salt="$LF_SALT"

oc create secret generic langfuse-nextauth-secret \
  --from-literal=nextauth-secret="$LF_NEXTAUTH_SECRET"

oc create secret generic langfuse-postgresql-auth \
  --from-literal=password="$PG_PASS" \
  --from-literal=postgres-password="$PG_PASS"

oc create secret generic langfuse-clickhouse-auth \
  --from-literal=password="$CH_PASS"

oc create secret generic langfuse-redis-auth \
  --from-literal=password="$REDIS_PASS"

oc create secret generic langfuse-s3-auth \
  --from-literal=rootUser="root" \
  --from-literal=rootPassword="$S3_ROOT_PASS"

echo ""
echo "Secrets created successfully."
