---
name: speckit-plan
description: Create implementation plan from feature spec
user-invocable: true
---

Create an implementation plan from the current feature spec.

## Workflow

1. **Setup**: Run `./scripts/bash/setup-plan.sh --json` to get:
   - FEATURE_SPEC: Path to the feature spec file
   - IMPL_PLAN: Path where the plan will be saved
   - SPECS_DIR: Directory containing specs
   - BRANCH: Current or suggested branch name

2. **Read context**:
   - Read FEATURE_SPEC
   - Read `.specify/memory/constitution.md`

3. **Create plan** following this structure:
   - Technical Context (from spec requirements)
   - Constitution Check (validate against principles)
   - Phase 0: Research (if needed)
   - Phase 1: Design & Contracts
     - data-model.md (entities, fields, relationships)
     - contracts/ (interfaces if external APIs)
     - quickstart.md (validation scenarios)

4. **Execute plan workflow**:
   - Extract entities from spec
   - Define data models
   - Document contracts
   - Create validation scenarios

5. **Generate tasks**: Create task breakdown in `.specify/tasks/{feature}-tasks.md`

6. **Report**: Return branch, plan path, and generated artifacts

## Key Rules

- Use absolute paths for filesystem operations
- Use project-relative paths for references in docs
- Follow constitution principles
- Create runnable validation scenarios

## Template

Use the structure from `.specify/templates/plan-template.md` if available.
