# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Specify-based project** that uses a structured, workflow-driven approach to feature development. Specify is a framework that enforces a constitutional development process with defined phases: specification → planning → task generation → implementation.

**Key Concept**: All feature work follows a strict workflow through slash commands that guide you through each phase. Do not implement features directly - use the workflow commands.

## Core Workflow Commands

The following slash commands execute the Specify workflow. **Always use these commands rather than implementing features manually:**

### 1. `/specify [feature description]`
Creates a new feature specification from a natural language description.
- Creates a new feature branch (numbered: `###-feature-name`)
- Generates `specs/[###-feature]/spec.md` with business requirements
- Focuses on WHAT users need, not HOW to implement
- Marks ambiguities with `[NEEDS CLARIFICATION]` tags

### 2. `/clarify`
Identifies underspecified areas in the current feature spec.
- Asks up to 5 targeted clarification questions
- Updates spec.md with answers to resolve ambiguities
- **Run this before `/plan` if the spec has unclear requirements**

### 3. `/plan [additional context]`
Generates the technical implementation plan from spec.md.
- Requires: spec.md must exist (from `/specify`)
- Outputs: research.md, data-model.md, contracts/, quickstart.md
- Updates this CLAUDE.md file incrementally with project details
- Performs constitutional compliance checks
- **Does NOT generate tasks.md** - that's done by `/tasks`

### 4. `/tasks`
Generates actionable, dependency-ordered tasks from the plan.
- Requires: plan.md must exist (from `/plan`)
- Outputs: tasks.md with numbered tasks (T001, T002, ...)
- Tasks are organized by phase: Setup → Tests → Core → Integration → Polish
- Marks parallelizable tasks with `[P]`

### 5. `/implement`
Executes all tasks defined in tasks.md.
- Requires: tasks.md must exist (from `/tasks`)
- Follows TDD approach: writes tests first, then implementation
- Marks completed tasks as `[X]` in tasks.md
- Respects task dependencies and parallel execution markers

### 6. `/analyze`
Performs cross-artifact consistency analysis.
- Validates spec.md, plan.md, and tasks.md for consistency
- Run after `/tasks` to catch issues before implementation

### 7. `/constitution`
Creates or updates the project constitution.
- Defines core development principles and constraints
- Template-based: edit `.specify/memory/constitution.md`

## Workflow Execution Pattern

**Standard feature development flow:**
```
1. /specify "feature description"
2. /clarify (if spec has [NEEDS CLARIFICATION] markers)
3. /plan
4. /tasks
5. /analyze (optional quality check)
6. /implement
```

## Important Execution Rules

### Script Execution
- All workflow scripts are in `.specify/scripts/bash/`
- Scripts must be run from repository root
- Scripts output JSON - parse and use the returned paths
- **Never run `create-new-feature.sh` or `setup-plan.sh` more than once per command**

### File Locations
- Feature specs: `specs/[###-feature-name]/`
- Each feature has: spec.md, plan.md, research.md, data-model.md, contracts/, tasks.md
- Templates: `.specify/templates/`
- Constitution: `.specify/memory/constitution.md`

### Agent File Updates
- The `/plan` command updates this CLAUDE.md file automatically via `update-agent-context.sh`
- Updates are incremental - new tech is added, manual edits preserved
- Kept under 150 lines for token efficiency
- Updates happen during Phase 1 of `/plan`

### Test-Driven Development
- Tests MUST be written before implementation
- Contract tests come from API contracts in `/contracts/`
- Integration tests come from user stories in spec.md
- All tests must fail before writing implementation code

### Constitutional Compliance
- Every plan is checked against `.specify/memory/constitution.md`
- Violations must be documented in the Complexity Tracking section
- Re-checked after Phase 1 design
- Complex features require justification

## Directory Structure

```
.
├── .claude/
│   └── commands/          # Slash command definitions
├── .specify/
│   ├── memory/
│   │   └── constitution.md  # Project constitution
│   ├── scripts/bash/        # Workflow automation scripts
│   └── templates/           # Templates for specs, plans, tasks
└── specs/                   # Feature specifications (created by workflow)
    └── [###-feature-name]/
        ├── spec.md          # Business requirements
        ├── plan.md          # Technical plan
        ├── research.md      # Technical decisions
        ├── data-model.md    # Entity definitions
        ├── contracts/       # API contracts
        └── tasks.md         # Implementation tasks
```

## Common Patterns

### When to Use Each Command
- **User asks for a new feature**: Start with `/specify`
- **Spec has unclear requirements**: Use `/clarify`
- **Need technical design**: Use `/plan`
- **Need task breakdown**: Use `/tasks`
- **Ready to code**: Use `/implement`
- **Quality check**: Use `/analyze`

### Handling Errors
- If a workflow command fails, check for missing prerequisites
- Each command's documentation shows required inputs
- Read error messages from scripts - they indicate missing files or branches

### Manual vs Automated Work
- **Never manually implement features** - always use `/specify` → `/plan` → `/tasks` → `/implement`
- Manual code changes are acceptable for: bug fixes, refactoring, debugging
- For new features, the workflow ensures constitutional compliance and completeness

## Git Workflow

- Each feature gets its own numbered branch: `###-feature-name`
- Branch is created automatically by `/specify` command
- Commit after completing each task during `/implement`
- Constitution ensures changes are reviewable and testable

## Notes for Claude Code

1. **Always check current branch** - feature work happens on feature branches
2. **Read the constitution** at `.specify/memory/constitution.md` to understand project constraints
3. **Parse JSON output** from bash scripts - they return absolute paths you must use
4. **Update task status** - mark tasks as `[X]` in tasks.md as you complete them
5. **Preserve manual edits** - when updating this file, keep content between `<!-- MANUAL ADDITIONS -->` markers
