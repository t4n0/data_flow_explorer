from data_flow_explorer import read, validate
import pytest


def call_sut(file_path: str):
    validate(read(file_path), file_path)


def test_validate_true_negatives():
    with pytest.raises(
        Exception,
        match='Input file "test/component_is_empty_string.json" failed validation. Component names must not be empty strings.',
    ):
        call_sut("test/component_is_empty_string.json")

    with pytest.raises(
        Exception,
        match="Input file \"test/component_is_not_unique.json\" failed validation. Component names must be unique. These names appear more than once: \\['Foo', 'Bar'\\].",
    ):
        call_sut("test/component_is_not_unique.json")

    with pytest.raises(
        Exception,
        match="Input file \"test/data_is_component.json\" failed validation. Data and component names must not be mixed. These names appear both as a component and a data name: \\['Foo', 'Bar'\\].",
    ):
        call_sut("test/data_is_component.json")

    with pytest.raises(
        Exception,
        match='Input file "test/data_is_empty_string.json" failed validation. Data names must not be empty strings.',
    ):
        call_sut("test/data_is_empty_string.json")

    with pytest.raises(
        Exception,
        match='Input file "test/schema_violated.json" failed validation. Schema violated. Additional properties are not allowed.*',
    ):
        call_sut("test/schema_violated.json")
