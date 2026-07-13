---
name: speckit-implement
description: Implement tasks from implementation plan
user-invocable: true
---

Implement the current feature based on the implementation plan.

## Workflow

1. **Setup**: Run `./scripts/bash/setup-implement.sh --json` to get:
   - FEATURE_SPEC: Path to the feature spec
   - IMPL_PLAN: Path to the implementation plan
   - TASKS_FILE: Path to tasks file
   - SPECS_DIR: Directory containing specs
   - BRANCH: Current branch

2. **Read context**:
   - Read FEATURE_SPEC
   - Read IMPL_PLAN
   - Read TASKS_FILE if exists
   - Read `.specify/memory/constitution.md`

3. **Implementation phases**:

   ### Phase 1: Project Structure
   - Create/modify files for data models
   - Create contracts/interfaces
   - Setup project scaffolding

   ### Phase 2: Core Implementation
   - Implement domain logic
   - Create services
   - Add validation

   ### Phase 3: Testing & Validation
   - Write unit tests
   - Write integration tests
   - Ensure coverage requirements

   ### Phase 4: Documentation
   - Update README if needed
   - Add inline documentation
   - Create usage examples

4. **Verify**:
   - Run linting (ruff, mypy)
   - Run tests
   - Check coverage

5. **Report**: Return implemented files, test results, and next steps

## Key Rules

- Follow constitution principles
- Write tests before/during implementation
- Maintain coverage ≥ 70%
- Use type hints everywhere
- Follow existing code style
- Never commit directly to main

## Template

Use tasks from `.specify/templates/tasks-template.md` if available.
