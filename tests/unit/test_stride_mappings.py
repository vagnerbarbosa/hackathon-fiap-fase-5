from pathlib import Path

import pytest

from core.stride_mappings import StrideMappingError, StrideMappings


def test_loads_component_and_data_flow_mappings() -> None:
    mappings = StrideMappings.from_file(Path("config/stride_mappings.yaml"))

    api_categories = {
        threat.category for threat in mappings.get_component_threats("api")
    }
    data_flow_categories = {
        threat.category for threat in mappings.get_data_flow_threats()
    }

    assert api_categories == {"S", "T", "R", "I", "D", "E"}
    assert data_flow_categories == {"T", "I", "D"}


def test_unknown_component_returns_empty_list() -> None:
    mappings = StrideMappings.from_file(Path("config/stride_mappings.yaml"))

    assert mappings.get_component_threats("unknown_component") == []


def test_invalid_yaml_fails_with_clear_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "stride_mappings.yaml"
    invalid_file.write_text("components: [", encoding="utf-8")

    with pytest.raises(StrideMappingError, match="Invalid YAML"):
        StrideMappings.from_file(invalid_file)


def test_invalid_category_fails_with_clear_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "stride_mappings.yaml"
    invalid_file.write_text(
        """
components:
  api:
    threats:
      - category: "X"
        description: "Invalid category."
        justification: "Invalid category still needs a justification."
data_flows:
  threats:
    - category: "T"
      description: "Valid data flow threat."
      justification: "Valid data flow threat needs a justification."
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(StrideMappingError, match="Invalid STRIDE categories: X"):
        StrideMappings.from_file(invalid_file)


def test_missing_justification_fails_with_clear_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "stride_mappings.yaml"
    invalid_file.write_text(
        """
components:
  api:
    threats:
      - category: "S"
        description: "Missing justification."
data_flows:
  threats:
    - category: "T"
      description: "Valid data flow threat."
      justification: "Data in transit needs integrity."
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(StrideMappingError, match="justification"):
        StrideMappings.from_file(invalid_file)
