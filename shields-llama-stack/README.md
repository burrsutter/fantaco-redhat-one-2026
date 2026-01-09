# Llama Stack Safety Shields

This directory contains example scripts demonstrating safety shields in Llama Stack. **Run these scripts in order 1 through 6** to learn shields step-by-step:

1. `1_list_models.py` - List available models
2. `2_list_safety_providers.py` - List safety providers
3. `3_list_shields.py` - List available shields
4. `4_register_shield.py` - Register a custom shield
5. `5_test_shield.py` - Test shield functionality
6. `6_agent_shield.py` - Use shields with agents

```bash
cd shields-llama-stack
source ../.venv/bin/activate
```

The scripts assume a LiteLLM MaaS backing of the Llama Stack

```bash
curl -sS https://litellm-prod.apps.maas.redhatworkshops.io/v1/models   -H "Authorization: Bearer sk-rjoHGt7bFsDNlsZZ112Mlw" | jq
```

```
python 1_list_models.py
# Continue with 2, 3, 4, 5, 6...
```

## Agents API vs Responses API

| Feature                     | Agents API | Responses API     |
|-----------------------------|------------|-------------------|
| Input/Output Safety Shields | Supported  | Not yet supported |

Agents let you specify input/output shields while Responses API does not (though support is planned).

When to use each:

- Agents API - Use when you need safety shields, audit trails, or compliance requirements
- Responses API - Use for conversation branching, dynamic per-call configuration, or OpenAI migration

There's also a planned future enhancement to use the Responses API as a backend for Agents, which would combine safety shields with the dynamic configuration capabilities of Responses.

https://github.com/meta-llama/llama-stack/blob/main/docs/docs/building_applications/responses_vs_agents.mdx
