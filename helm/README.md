1. Deploy the Fantaco microservices and DB
```bash
helm install fantaco-app ./fantaco-app
```
2. Deploy Fantaco MCP servers to access microservices APIs
```bash
helm install fantaco-mcp ./fantaco-mcp
```
3. Deploy Langgraph agent
```bash
helm install fantaco-agent ./fantaco-agent
```
