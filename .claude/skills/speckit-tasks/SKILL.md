---
name: speckit-tasks
description: Generate actionable tasks breakdown from feature spec and plan
user-invocable: true
---

Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.

## Workflow

1. **Setup**: Run `./scripts/bash/setup-plan.sh --json` from repo root and parse FEATURE_DIR, TASKS_TEMPLATE, and AVAILABLE_DOCS list.

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (interface contracts), research.md (decisions), quickstart.md (test scenarios)
   - **IF EXISTS**: Load `/memory/constitution.md` for project principles and governance constraints

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map interface contracts to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story

4. **Generate tasks.md**: Create tasks file in `.specify/tasks/{feature}-tasks.md` with:
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites)
   - Phase 3+: One phase per user story
   - Final Phase: Polish & cross-cutting concerns

## Task Format

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

Examples:
- ✅ `- [ ] T001 Create project structure per implementation plan`
- ✅ `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ `- [ ] T012 [P] [US1] Create User model in src/models/user.py`

## Key Rules

- Tasks organized by user story to enable independent implementation
- Each task must have clear file path
- Mark parallelizable tasks with [P]
- Mark story-specific tasks with [US1], [US2], etc.

## Done When

- [ ] tasks.md generated with all phases, task IDs, and file paths
- [ ] Completion reported with task count, story breakdown, and MVP scope
