---
name: speckit-constitution
description: Create or update project constitution
user-invocable: true
---

Create or update the project constitution defining core principles.

## Workflow

1. **Read current constitution** at `.specify/memory/constitution.md`

2. **Collect/derive values**:
   - Use user input if provided
   - Infer from repo context (README, docs)
   - Update version (semantic versioning):
     - MAJOR: Breaking governance changes
     - MINOR: New principles
     - PATCH: Clarifications/fixes

3. **Update constitution**:
   - Replace placeholder tokens with concrete text
   - Define core principles with rationale
   - Add governance section

4. **Sync templates**: Ensure templates reference updated principles

5. **Generate sync report**: Document changes and follow-ups

6. **Write**: Save to `.specify/memory/constitution.md`

## Format

Use structure from `.specify/templates/constitution-template.md`:

- Core Principles section
- Each principle: name + description + rationale
- Governance section (versioning, amendments)

## Done When

- Constitution updated with concrete values
- No unexplained placeholder tokens
- Version bumped appropriately
- Sync impact report generated
