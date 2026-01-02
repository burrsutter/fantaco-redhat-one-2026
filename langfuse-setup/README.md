# Langfuse 

## Langfuse Localhost

Ingredients:
```bash
MacBook (localhost)
├── Podman machine (Linux VM)
│   ├── Langfuse Web UI     http://localhost:3000
│   ├── Langfuse Worker
│   ├── Postgres
│   ├── ClickHouse
│   ├── Minio
│   └── Redis
├── MCP servers (host or containers)
├── LangGraph agents (host or containers)
└── Llama Stack server (host or container)
```

```bash
brew install podman podman-compose
podman machine start
podman machine list
```

```
NAME                    VM TYPE     CREATED       LAST UP             CPUS        MEMORY      DISK SIZE
podman-machine-default  applehv     3 months ago  Currently starting  4           16GiB       100GiB
```

```bash
podman info
podman ps
```

Since I normally run postgress view `brew` and I will need to stop it before trying the compose method to run everything

```bash
brew services stop postgresql@14
```

```bash
brew services list
```

```
Name          Status  User    File
kafka         started bsutter ~/Library/LaunchAgents/homebrew.mxcl.kafka.plist
ollama        none
podman        none
postgresql@14 none
unbound       none
zookeeper     started bsutter ~/Library/LaunchAgents/homebrew.mxcl.zookeeper.plist
```

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
```

```bash
ls *.yml
```

```
docker-compose.build.yml			docker-compose.dev-redis-cluster.yml	docker-compose.yml
docker-compose.dev-azure.yml		docker-compose.dev.yml
```

```bash
podman compose up
```

```bash
podman compose ps
```

```
CONTAINER ID  IMAGE                                          COMMAND               CREATED         STATUS                   PORTS                                                         NAMES
2a053acda112  docker.io/clickhouse/clickhouse-server:latest                        50 seconds ago  Up 50 seconds (healthy)  127.0.0.1:8123->8123/tcp, 127.0.0.1:9000->9000/tcp, 9009/tcp  langfuse-clickhouse-1
12377208f0ed  cgr.dev/chainguard/minio:latest                -c mkdir -p /data...  50 seconds ago  Up 50 seconds (healthy)  127.0.0.1:9091->9001/tcp, 0.0.0.0:9090->9000/tcp              langfuse-minio-1
d4de78e03a5a  docker.io/library/postgres:17                  postgres              50 seconds ago  Up 50 seconds (healthy)  127.0.0.1:5432->5432/tcp                                      langfuse-postgres-1
4889a30385e9  docker.io/library/redis:7                      --requirepass myr...  50 seconds ago  Up 50 seconds (healthy)  127.0.0.1:6379->6379/tcp                                      langfuse-redis-1
3b4244cd77d4  docker.io/langfuse/langfuse:3                  /bin/sh -c if [ -...  50 seconds ago  Up 43 seconds            0.0.0.0:3000->3000/tcp                                        langfuse-langfuse-web-1
4421bda243b4  docker.io/langfuse/langfuse-worker:3           node worker/dist/...  50 seconds ago  Up 43 seconds            127.0.0.1:3030->3030/tcp                                      langfuse-langfuse-worker-1
```

Note: the unassisted `podman compose up` did not correctly start postgres due to authentication errors, I needed Claude Code to figure it out.

```bash
open http://localhost:3000
```

![Langfuse Login](images/login-1.png)

Sign-Up

In the Langfuse UI:
	1.	Create Organization
	2.	Create Project
	3.	Go to: Project -> Settings -> API Keys

See [screenshots.md](screenshots.md) for detailed UI screenshots.


Create a `.env` with:
*LANGFUSE_SECRET_KEY*
*LANGFUSE_PUBLIC_KEY*
*LANGFUSE_BASE_URL*



If you forget the password:

```bash
podman compose down -v
podman compose up
```

## Langfuse Setup - OpenShift

This folder and sub-project include the instructions to run LangFuse on OpenShift and interate an example LangGraph-based agent into the traces capabilities of LangFuse. 


### Installation: OpenShift

As the Cluster Admin

```bash
oc new-project langfuse

helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update
```

```bash
LF_SALT="$(openssl rand -hex 16)"
LF_NEXTAUTH_SECRET="$(openssl rand -hex 32)"
PG_PASS="$(openssl rand -hex 16)"
CH_PASS="$(openssl rand -hex 16)"
REDIS_PASS="$(openssl rand -hex 16)"
S3_ROOT_PASS="$(openssl rand -hex 16)"
```

```bash
oc -n langfuse create secret generic langfuse-general \
  --from-literal=salt="$LF_SALT"

oc -n langfuse create secret generic langfuse-nextauth-secret \
  --from-literal=nextauth-secret="$LF_NEXTAUTH_SECRET"

oc -n langfuse create secret generic langfuse-postgresql-auth \
  --from-literal=password="$PG_PASS" \
  --from-literal=postgres-password="$PG_PASS"

oc -n langfuse create secret generic langfuse-clickhouse-auth \
  --from-literal=password="$CH_PASS"

oc -n langfuse create secret generic langfuse-redis-auth \
  --from-literal=password="$REDIS_PASS"

oc -n langfuse create secret generic langfuse-s3-auth \
  --from-literal=rootUser="root" \
  --from-literal=rootPassword="$S3_ROOT_PASS"
```

```bash
helm install langfuse langfuse/langfuse -n langfuse -f values-openshift.yaml
```

```bash
oc get pods -n langfuse
```

```
NAME                               READY   STATUS              RESTARTS   AGE
langfuse-clickhouse-shard0-0       0/1     ContainerCreating   0          6s
langfuse-clickhouse-shard0-1       0/1     ContainerCreating   0          6s
langfuse-clickhouse-shard0-2       0/1     ContainerCreating   0          6s
langfuse-postgresql-0              0/1     ContainerCreating   0          6s
langfuse-redis-primary-0           0/1     ContainerCreating   0          6s
langfuse-s3-5fb6c8f845-7dqz9       0/1     ContainerCreating   0          6s
langfuse-web-77f5988d59-rqphb      0/1     ContainerCreating   0          6s
langfuse-worker-74694f948f-c6pg5   0/1     ContainerCreating   0          6s
langfuse-zookeeper-0               0/1     ContainerCreating   0          6s
langfuse-zookeeper-1               0/1     Pending             0          6s
langfuse-zookeeper-2               0/1     ContainerCreating   0          6s
```

When all pods have started successfully

```bash
oc expose service langfuse-web -n langfuse
```

```bash
export LANGFUSE_URL="http://$(oc get route -l app.kubernetes.io/name=langfuse -o jsonpath='{.items[0].spec.host}')"
echo $LANGFUSE_URL
```

You need to update the values-openshift.yaml otherwise the sign-up login process will redirect to the incorrect URL (e.g. localhost:3000)

```
  langfuse:
    nextauth:
      url: "PLACEHOLDER_URL"
```


MacOS

```bash
sed -i '' "s|PLACEHOLDER_URL|$LANGFUSE_URL|g" values-openshift.yaml
```

Linux

```bash
sed -i "s|PLACEHOLDER_URL|$LANGFUSE_URL|g" values-openshift.yaml
```

Update the deployment

```bash
helm upgrade langfuse langfuse/langfuse -n langfuse -f values-openshift.yaml
```

```bash
oc rollout restart deployment langfuse-web -n langfuse
```


```bash
open $LANGFUSE_URL
```

### API Key

In the Langfuse UI:
  1.  Create a new Account
	2.	Create Organization
	3.	Create Project
	4.	Go to: Project -> Settings -> API Keys

See [screenshots.md](screenshots.md)


### Postgres Setup for FantaCo if needed

```bash
psql -h localhost -p 5432 -U postgres -d postgres
```

```psql
\l
```

```
                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges
-----------+----------+----------+------------+------------+-----------------------
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 |
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
(3 rows)
```

```psql
CREATE DATABASE fantaco_customer;
CREATE DATABASE fantaco_finance;
```

```psql
\l
```

```
                                    List of databases
       Name       |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges
------------------+----------+----------+------------+------------+-----------------------
 fantaco_customer | postgres | UTF8     | en_US.utf8 | en_US.utf8 |
 fantaco_finance  | postgres | UTF8     | en_US.utf8 | en_US.utf8 |
 postgres         | postgres | UTF8     | en_US.utf8 | en_US.utf8 |
 template0        | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
                  |          |          |            |            | postgres=CTc/postgres
 template1        | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
                  |          |          |            |            | postgres=CTc/postgres
(5 rows)
```
