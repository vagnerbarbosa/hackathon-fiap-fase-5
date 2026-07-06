# Tasks — Spec 000: Contratos de Domínio

**Branch**: `feature/000-domain-contracts-impl`  
**Plan**: `.specify/plans/000-20260706-193018-plan.md`

---

## Phase 1: Project Structure

### Task 1.1: Create Domain Package
**File**: `src/domain/__init__.py`
**Status**: ⬜  
**Description**: Create empty init file to make domain a proper Python package
**Acceptance**:
- File exists and is empty or contains package docstring
- `from domain import models` works after Task 1.2

---

## Phase 2: Core Implementation

### Task 2.1: Implement Detection Models
**File**: `src/domain/models.py` (lines 1-59)  
**Status**: ⬜  
**Description**: Create Pydantic models for detection domain
**Models to implement**:
- `BoundingBox` (x_min, y_min, x_max, y_max: int)
- `Point` (x, y: int)
- `DetectedComponent` (id, type, confidence, bbox, center)
- `DataFlow` (source_id, target_id, direction, inferred)
- `ArchitectureGraph` (components, data_flows, trust_boundaries)
**Acceptance**:
- All models defined with proper type hints
- confidence field uses Field(ge=0.0, le=1.0)
- direction uses Literal["unidirectional", "bidirectional"]

### Task 2.2: Implement STRIDE Models
**File**: `src/domain/models.py` (lines 61-78)  
**Status**: ⬜  
**Description**: Create Severity enum and Threat model
**Models to implement**:
- `Severity(str, Enum)`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `Threat` (id, category, component_id, component_type, description, severity, affected_data_flows)
**Acceptance**:
- Severity is a proper Python Enum
- Threat.category accepts "S", "T", "R", "I", "D", "E"
- affected_data_flows has default value []

### Task 2.3: Implement Vulnerability Models
**File**: `src/domain/models.py` (lines 80-98)  
**Status**: ⬜  
**Description**: Create Countermeasure and EnrichedThreat models
**Models to implement**:
- `Countermeasure` (title, description, owasp_ref)
- `EnrichedThreat` (extends Threat fields + cwe_id, cwe_name, cve_ids, countermeasures)
**Acceptance**:
- owasp_ref is Optional[str]
- cve_ids is list[str] with default []
- countermeasures is list[Countermeasure] with default []

### Task 2.4: Implement Job Models
**File**: `src/domain/models.py` (lines 100-116)  
**Status**: ⬜  
**Description**: Create JobStatus enum and Job model
**Models to implement**:
- `JobStatus(str, Enum)`: PENDING, PROCESSING, COMPLETED, FAILED
- `Job` (id, status, input_image_path, output_report_path, error_message, created_at, updated_at)
**Acceptance**:
- id field uses Field(default_factory=uuid4)
- output_report_path is Optional[str]
- error_message is Optional[str]
- datetime fields use timezone-aware datetime

---

## Phase 3: Mocks for Parallel Development

### Task 3.1: Create Mocks Package
**File**: `tests/mocks/__init__.py`  
**Status**: ⬜  
**Description**: Create empty init file for mocks package

### Task 3.2: Create ArchitectureGraph Mock
**File**: `tests/mocks/fake_architecture_graph.py`  
**Status**: ⬜  
**Description**: Create realistic mock for Spec 004/006 testing
**Requirements**:
- Import models from domain.models
- Create 3 components: user, api, database
- Create 2 data flows connecting them
- Define 2 trust boundaries
- Export `fake_graph` variable
**Acceptance**:
- Can run: `python tests/mocks/fake_architecture_graph.py`
- Validates without Pydantic errors

### Task 3.3: Create Threats Mock
**File**: `tests/mocks/fake_threats.py`  
**Status**: ⬜  
**Description**: Create mock threats for Spec 005/006 testing
**Requirements**:
- Import Threat, Severity from domain.models
- Create 3 threats with different categories (T, I, D)
- Different severity levels (CRITICAL, HIGH, MEDIUM)
- Export `fake_threats` list
**Acceptance**:
- Can run: `python tests/mocks/fake_threats.py`
- All threats validate correctly

### Task 3.4: Create EnrichedThreats Mock
**File**: `tests/mocks/fake_enriched_threats.py`  
**Status**: ⬜  
**Description**: Create mock enriched threats for Spec 006 testing
**Requirements**:
- Import EnrichedThreat, Severity, Countermeasure
- Create threat with CWE/CVE references
- Add countermeasures with OWASP references
- Export `fake_enriched` list
**Acceptance**:
- Can run: `python tests/mocks/fake_enriched_threats.py`
- Validates with countermeasures

### Task 3.5: Create Job Mock
**File**: `tests/mocks/fake_job.py`  
**Status**: ⬜  
**Description**: Create mock job for Spec 006 testing
**Requirements**:
- Import Job, JobStatus
- Create completed job with paths
- Use timezone.utc for datetime
- Export `fake_job` variable
**Acceptance**:
- Can run: `python tests/mocks/fake_job.py`
- Validates without errors

---

## Phase 4: Validation

### Task 4.1: Import Test
**Status**: ⬜  
**Description**: Verify all models import correctly
**Command**:
```bash
python -c "from domain.models import *; print('OK')"
```
**Acceptance**: Prints "OK" without errors

### Task 4.2: Validation Test
**Status**: ⬜  
**Description**: Verify validation works for confidence bounds
**Command**:
```python
python -c "
from domain.models import DetectedComponent, BoundingBox, Point
try:
    c = DetectedComponent(id='1', type='x', confidence=1.5, bbox=BoundingBox(x_min=0,y_min=0,x_max=1,y_max=1), center=Point(x=0,y=0))
    print('FAIL: should have raised')
except:
    print('OK')
"
```
**Acceptance**: Prints "OK"

### Task 4.3: Mocks Test
**Status**: ⬜  
**Description**: Run all mock files
**Commands**:
```bash
python tests/mocks/fake_architecture_graph.py && echo "OK: architecture"
python tests/mocks/fake_threats.py && echo "OK: threats"
python tests/mocks/fake_enriched_threats.py && echo "OK: enriched"
python tests/mocks/fake_job.py && echo "OK: job"
```
**Acceptance**: All print OK

---

## Done When

- [ ] Task 1.1: Domain package created
- [ ] Task 2.1: Detection models implemented
- [ ] Task 2.2: STRIDE models implemented
- [ ] Task 2.3: Vulnerability models implemented
- [ ] Task 2.4: Job models implemented
- [ ] Task 3.1: Mocks package created
- [ ] Task 3.2: ArchitectureGraph mock created
- [ ] Task 3.3: Threats mock created
- [ ] Task 3.4: EnrichedThreats mock created
- [ ] Task 3.5: Job mock created
- [ ] Task 4.1: Import test passed
- [ ] Task 4.2: Validation test passed
- [ ] Task 4.3: Mocks test passed

---

*Tasks generated from Implementation Plan*
