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


### Installation

```bash
kubectl create namespace langfuse

helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update
```

```bash
helm install langfuse langfuse/langfuse \
  --namespace langfuse
```

```bash
oc expose service svc/langfuse-web -n langfluse
```

#### API Key

In the Langfuse UI:
	1.	Create Organization
	2.	Create Project
	3.	Go to: Project -> Settings -> API Keys

See [screenshots.md](screenshots.md)


### Postgres

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
