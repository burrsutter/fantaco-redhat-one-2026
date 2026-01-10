#!/bin/bash
# Fix ClickHouse nondeterministic mutations error for Langfuse trace deletion
# Uses the current oc project - no arguments needed

# Get current namespace from oc project
NAMESPACE=$(oc project -q)
if [ -z "$NAMESPACE" ]; then
    echo "Error: Could not determine current namespace"
    echo "Make sure you are logged in and have a project selected"
    exit 1
fi

echo "Patching ClickHouse ConfigMap in namespace: $NAMESPACE"

# Create the updated config
cat > /tmp/clickhouse-config-patch.xml << EOF
<clickhouse>
  <!-- Macros -->
  <macros>
    <shard from_env="CLICKHOUSE_SHARD_ID"></shard>
    <replica from_env="CLICKHOUSE_REPLICA_ID"></replica>
    <layer>langfuse-clickhouse</layer>
  </macros>
  <!-- Log Level -->
  <logger>
    <level>information</level>
  </logger>
  <!-- Allow nondeterministic mutations for Langfuse trace deletion -->
  <profiles>
    <default>
      <allow_nondeterministic_mutations>1</allow_nondeterministic_mutations>
    </default>
  </profiles>
  <!-- Cluster configuration - Any update of the shards and replicas requires helm upgrade -->
  <remote_servers>
    <default>
      <shard>
          <replica>
              <host>langfuse-clickhouse-shard0-0.langfuse-clickhouse-headless.${NAMESPACE}.svc.cluster.local</host>
              <port>9000</port>
              <user from_env="CLICKHOUSE_ADMIN_USER"></user>
              <password from_env="CLICKHOUSE_ADMIN_PASSWORD"></password>
          </replica>
          <replica>
              <host>langfuse-clickhouse-shard0-1.langfuse-clickhouse-headless.${NAMESPACE}.svc.cluster.local</host>
              <port>9000</port>
              <user from_env="CLICKHOUSE_ADMIN_USER"></user>
              <password from_env="CLICKHOUSE_ADMIN_PASSWORD"></password>
          </replica>
          <replica>
              <host>langfuse-clickhouse-shard0-2.langfuse-clickhouse-headless.${NAMESPACE}.svc.cluster.local</host>
              <port>9000</port>
              <user from_env="CLICKHOUSE_ADMIN_USER"></user>
              <password from_env="CLICKHOUSE_ADMIN_PASSWORD"></password>
          </replica>
      </shard>
    </default>
  </remote_servers>
  <!-- Zookeeper configuration -->
  <zookeeper>
    <node>
      <host from_env="KEEPER_NODE_0"></host>
      <port>2181</port>
    </node>
    <node>
      <host from_env="KEEPER_NODE_1"></host>
      <port>2181</port>
    </node>
    <node>
      <host from_env="KEEPER_NODE_2"></host>
      <port>2181</port>
    </node>
  </zookeeper>
  <listen_host>0.0.0.0</listen_host>
  <listen_host>::</listen_host>
  <listen_try>1</listen_try>
</clickhouse>
EOF

# Update the ConfigMap
echo "Updating ConfigMap..."
oc create configmap langfuse-clickhouse -n "$NAMESPACE" \
  --from-file=00_default_overrides.xml=/tmp/clickhouse-config-patch.xml \
  --dry-run=client -o yaml | oc apply -f -

# Restart ClickHouse pods
echo "Restarting ClickHouse StatefulSet..."
oc rollout restart statefulset/langfuse-clickhouse-shard0 -n "$NAMESPACE"

echo "Waiting for rollout to complete..."
oc rollout status statefulset/langfuse-clickhouse-shard0 -n "$NAMESPACE" --timeout=300s

echo "Done! ClickHouse is now configured to allow nondeterministic mutations."

# Cleanup
rm -f /tmp/clickhouse-config-patch.xml
