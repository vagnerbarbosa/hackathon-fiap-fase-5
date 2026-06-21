---
name: speckit-specify
description: Create feature specification
user-invocable: true
---

Create a new feature specification based on user description.

## Workflow

1. **Generate short name** (2-4 words) from feature description

2. **Create feature directory**:
   - Check `.specify/init-options.json` for `feature_numbering`
   - If `"timestamp"`: use `YYYYMMDD-HHMMSS` prefix
   - If `"sequential"` (default): use next 3-digit number
   - Create: `specs/<prefix>-<short-name>/`

3. **Read templates**:
   - Load `.specify/templates/spec-template.md`
   - Load `.specify/memory/constitution.md` (if exists)

4. **Create spec**:
   - Parse user description
   - Extract: actors, actions, data, constraints
   - Fill template sections:
     - Context/Motivation
     - Objective
     - Requirements (testable)
     - Success Criteria (measurable)
     - User Scenarios
     - Assumptions
   - Save to `specs/<dir>/spec.md`

5. **Create checklist** (if needed):
   - Quality validation checklist in `specs/<dir>/checklist.md`

6. **Report**: Return feature directory and spec file path

## Format

Follow structure from `.specify/templates/spec-template.md`:

- Context/Motivation (the "why")
- Objective (the "what")
- Requirements (testable, no implementation details)
- Success Criteria (measurable outcomes)
- User Scenarios (flow examples)
- Assumptions
- Acceptance Criteria

## Key Rules

- Focus on **WHAT** and **WHY**, not **HOW**
- No implementation details (languages, frameworks)
- Requirements must be testable
- Maximum 3 [NEEDS CLARIFICATION] markers
- Document assumptions

## Done When

- Spec written to `specs/<dir>/spec.md`
- All mandatory sections completed
- Requirements are testable
- Success criteria are measurable
