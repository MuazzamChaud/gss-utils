import json
from pathlib import Path
from typing import List

import pytest
import pandas as pd
from csvcubed.models.validationerror import ValidationError
from dateutil import parser
from csvcubed.utils.qb.cube import get_columns_of_dsd_type
from csvcubed.utils.qb.validation.cube import validate_qb_component_constraints
from csvcubed.models.cube import *
from csvcubeddevtools.helpers.file import get_test_cases_dir


config_loader_test_cases_dir = Path(
    get_test_cases_dir().absolute() / "configloaders"
)

from gssutils.csvcubedintegration.configloaders.infojson import get_cube_from_info_json

def test_csv_cols_assumed_dimensions():
    """
    If a column isn't defined, assume it is a new local dimension.

    Assume that if a column isn't defined in the info.json `transform.columns` section, then it is a
    new locally defined dimension.

    Assert that the newly defined dimension has a codelist created from the values in the CSV.
    """

    config_path = Path(config_loader_test_cases_dir / "info.json")
    data_path = Path(config_loader_test_cases_dir / "data.csv")

    cube, _, _ = get_cube_from_info_json(
        config_path, data_path
    )

    matching_columns = [
        c for c in cube.columns if hasattr(c, "csv_column_title") and c.csv_column_title == "Undefined Column"
    ]
    assert len(matching_columns) == 1
    undefined_column_assumed_definition: CsvColumn = matching_columns[0]

    if not isinstance(undefined_column_assumed_definition, QbColumn):
        raise Exception("Incorrect type")

    assert type(undefined_column_assumed_definition.structural_definition) == NewQbDimension

    new_dimension: NewQbDimension = undefined_column_assumed_definition.structural_definition
    assert new_dimension.code_list is not None

    if not isinstance(new_dimension.code_list, NewQbCodeList):
        raise Exception("Incorrect type")

    newly_defined_concepts = list(new_dimension.code_list.concepts)

    assert len(newly_defined_concepts) == 1

    new_concept = newly_defined_concepts[0]
    assert "Undefined Column Value" == new_concept.label

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert_num_validation_errors(errors, 0)


def test_multiple_measures_and_units_loaded_in_uri_template():
    """
    multi-measure-unit-data.csv has multiple measures and multiple units

    The JSON schema for the info.json files which defines all of the possible properties an info.json can have is
    to be found at <https://github.com/GSS-Cogs/family-schemas/blob/main/dataset-schema.json>.
    """

    config_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-unit-info.json")
    data_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-unit-data.csv")


    cube, _, _ = get_cube_from_info_json(
        config_path, data_path
    )

    """Measure URI"""

    expected_measure_uris = [
        "http://gss-data.org.uk/def/x/one-litre-and-less",
        "http://gss-data.org.uk/def/x/more-than-one-litre",
        "http://gss-data.org.uk/def/x/number-of-bottles",
    ]
    measure_column = cube.columns[1]

    assert type(measure_column) == QbColumn
    assert type(measure_column.structural_definition) == QbMultiMeasureDimension

    actual_measure_uris = [x.measure_uri for x in measure_column.structural_definition.measures]
    assert len(expected_measure_uris) == len(actual_measure_uris)
    assert not (set(expected_measure_uris) ^ set(actual_measure_uris))

    # """Unit URI"""

    unit_column = cube.columns[2]

    assert type(unit_column) == QbColumn
    assert type(unit_column.structural_definition) == QbMultiUnits

    expected_unit_uris = [
        "http://gss-data.org.uk/def/concept/measurement-units/count",
        "http://gss-data.org.uk/def/concept/measurement-units/percentage",
    ]

    actual_unit_uris = [x.unit_uri for x in unit_column.structural_definition.units]
    assert len(expected_unit_uris) == len(actual_unit_uris)
    assert not (set(expected_unit_uris) ^ set(actual_unit_uris))

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert_num_validation_errors(errors, 0)


def test_cube_metadata_extracted_from_info_json():

    """Metadata - ['base_uri', 'creator', 'description', 'from_dict', 'issued', 'keywords', 'landing_page',
    'license', 'public_contact_point', 'publisher', 'summary', 'themes', 'title',
    'uri_safe_identifier', 'validate']"""


    config_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-unit-info.json")
    data_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-unit-data.csv")

    cube, _, _ = get_cube_from_info_json(
        config_path, data_path
    )

    # Creator - pass

    expected_creator = "https://www.gov.uk/government/organisations/hm-revenue-customs"
    actual_creator = cube.metadata.creator_uri
    assert expected_creator == actual_creator

    # Description - pass

    expected_description = (
        "All bulletins provide details on percentage of one litre or less & more than "
        "one litre bottles. This information is provided on a yearly basis."
    )
    actual_description = cube.metadata.description
    assert expected_description == actual_description

    # issue_date - pass

    expected_issued_date = parser.parse("2019-02-28")
    actual_issued_date = cube.metadata.dataset_issued
    assert actual_issued_date == expected_issued_date

    # keywords - pass
    # There's currently no `keywords` property to map from the info.json.
    expected_keywords = []
    actual_keywords = cube.metadata.keywords
    assert len(expected_keywords) == len(actual_keywords)
    assert not (set(expected_keywords) ^ set(actual_keywords))

    # landingpage - pass

    expected_landingpage = ["https://www.gov.uk/government/statistics/bottles-bulletin"]
    actual_landingpage = cube.metadata.landing_page_uris
    assert expected_landingpage == actual_landingpage

    # license - pass
    # Surprisingly the info.json schema doesn't allow a licence property just yet.
    expected_license = None
    actual_license = cube.metadata.license_uri
    assert expected_license == actual_license

    # public_contact_point - pass
    # The info.json schema doesn't allow a public_contact_point property just yet

    expected_public_contact_point = None
    actual_public_contact_point = cube.metadata.public_contact_point_uri
    assert expected_public_contact_point == actual_public_contact_point

    # publisher - pass

    expected_publisher = (
        "https://www.gov.uk/government/organisations/hm-revenue-customs"
    )
    actual_publisher = cube.metadata.publisher_uri
    assert expected_publisher == actual_publisher

    # summary - pass
    # The info.json schema doesn't allow a summary property just yet

    expected_summary = None
    actual_summary = cube.metadata.summary
    assert expected_summary == actual_summary

    # themes - pass
    # It's the families property

    expected_themes = ["http://gss-data.org.uk/def/gdp#trade"]
    actual_themes = [str(t) for t in cube.metadata.theme_uris]
    assert len(expected_themes) == len(actual_themes)
    assert not (set(expected_themes) ^ set(actual_themes))

    # title - pass

    expected_title = "bottles"
    actual_title = cube.metadata.title
    assert expected_title == actual_title

    # uri_safe_identifier - pass

    expected_uri_safe_identifier = "bottles-bulletin"
    actual_uri_safe_identifier = cube.metadata.uri_safe_identifier
    assert expected_uri_safe_identifier == actual_uri_safe_identifier

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert_num_validation_errors(errors, 0)


def test_single_measure_obs_val_unit_measure_data_type():
    """
    Test that the datatype, unit & measure are correctly extracted from a single-measure dataset's info.json file
    """

    config_path = Path(config_loader_test_cases_dir / "info.json")
    data_path = Path(config_loader_test_cases_dir / "data.csv")

    cube, _, _ = get_cube_from_info_json(
        config_path, data_path
    )

    obs_val_cols = get_columns_of_dsd_type(cube, QbSingleMeasureObservationValue)
    assert len(obs_val_cols) == 1
    obs_val = obs_val_cols[0].structural_definition
    assert isinstance(obs_val, QbSingleMeasureObservationValue)

    unit = obs_val.unit
    assert unit is not None
    assert isinstance(unit, ExistingQbUnit)
    assert (
        unit.unit_uri
        == "http://gss-data.org.uk/def/concept/measurement-units/gbp-million"
    )

    measure = obs_val.measure
    assert isinstance(measure, ExistingQbMeasure)
    assert measure.measure_uri == "http://gss-data.org.uk/def/measure/trade"

    assert obs_val.data_type == "double"


def test_definitions_loaded_for_columns_not_in_data():
    """
    Ensure that column definitions from an info.json file as loaded even if the column isn't defined in the initial
    loaded data.

    This is primarily to ensure that cube validation highlights that they've defined columns which aren't in the data.
    """

    config_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-unit-info.json")
    data_path = Path(config_loader_test_cases_dir
        / "multi-measure-multi-unit-test-files"
        / "multi-measure-missing-unit-data.csv")

    cube, _, _ = get_cube_from_info_json(
        config_path, data_path
    )

    errors = cube.validate()

    assert_num_validation_errors(errors, 1)
    error = errors[0]
    assert isinstance(error, ColumnNotFoundInDataError)
    assert error.csv_column_title == "Unit"


def assert_num_validation_errors(
    errors: List[ValidationError], num_errors_expected: int
):
    assert len(errors) == num_errors_expected, ", ".join([e.message for e in errors])


if __name__ == "__main__":
    pytest.main()
