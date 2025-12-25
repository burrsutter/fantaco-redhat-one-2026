  

  | Feature                     | Agents API | Responses API     |
  |-----------------------------|------------|-------------------|
  | Input/Output Safety Shields | Supported  | Not yet supported |

  Agents let you specify input/output shields whereas Responses do not (though support is planned).

  When to use each:

  - Agents API - Use when you need safety shields, audit trails, or compliance requirements
  - Responses API - Use for conversation branching, dynamic per-call configuration, or OpenAI migration

  There's also a planned future enhancement to use the Responses API as a backend for Agents, which would combine safety shields with the dynamic configuration capabilities of Responses.

  https://github.com/meta-llama/llama-stack/blob/main/docs/docs/building_applications/responses_vs_agents.mdx

  