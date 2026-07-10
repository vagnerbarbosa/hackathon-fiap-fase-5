---
name: speckit-checklist
description: Generate quality validation checklist for requirements
user-invocable: true
---

Generate a custom checklist for validating requirements quality ("Unit Tests for English").

## Purpose

Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** - they validate the quality, clarity, and completeness of requirements in a given domain.

**NOT for verification/testing**:
- ❌ NOT "Verify the button clicks correctly"
- ❌ NOT "Test error handling works"

**FOR requirements quality validation**:
- ✅ "Are visual hierarchy requirements defined?" [Completeness]
- ✅ "Is 'prominent display' quantified?" [Clarity]
- ✅ "Are hover state requirements consistent?" [Consistency]

## Workflow

1. **Setup**: Run `./scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR.

2. **Load context**:
   - Read spec.md: Feature requirements and scope
   - Read plan.md (if exists): Technical details
   - Read `/memory/constitution.md` for project principles

3. **Generate checklist**:
   - Create `specs/features/{feature}/checklists/` directory
   - Generate checklist file: `[domain].md` (e.g., `ux.md`, `api.md`, `security.md`)
   - Number items starting from CHK001 (or continue from existing)

## Checklist Categories

- **Requirement Completeness**: Are all necessary requirements documented?
- **Requirement Clarity**: Are requirements specific and unambiguous?
- **Requirement Consistency**: Do requirements align without conflicts?
- **Acceptance Criteria Quality**: Are success criteria measurable?
- **Scenario Coverage**: Are all flows/cases addressed?
- **Edge Case Coverage**: Are boundary conditions defined?
- **Non-Functional Requirements**: Performance, Security, Accessibility?

## Item Format

```markdown
- [ ] CHK001 - Are [requirement type] defined for [scenario]? [Quality Dimension, Spec §X.Y]
```

Examples:
- ✅ `- [ ] CHK001 - Are error handling requirements defined for all API failure modes? [Completeness]`
- ✅ `- [ ] CHK002 - Is 'fast loading' quantified with specific timing thresholds? [Clarity, Spec §NFR-2]`
- ✅ `- [ ] CHK003 - Are rollback requirements defined for migration failures? [Gap]`

## Key Rules

- Ask about requirements quality, NOT implementation behavior
- Use question format: "Are requirements defined/specified/documented?"
- Include traceability: `[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`, `[Conflict]`
- Minimum 80% of items must include traceability reference

## Done When

- [ ] Checklist file created or appended
- [ ] All items follow checklist format with CHK IDs
- [ ] Items test requirements quality, NOT implementation
