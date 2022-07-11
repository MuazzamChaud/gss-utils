"""
Info.json Loader
----------------

A loader for the info.json file format.
"""
import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json
import copy
import pandas as pd
import uritemplate
from dateutil import parser
from csvcubedmodels.rdf.namespaces import GOV, GDP
from csvcubed.models.cube import *
from gssutils.utils import pathify
from csvcubed.utils.uri import csvw_column_name_safe, uri_safe
from csvcubed.utils.dict import get_from_dict_ensure_exists, get_with_func_or_none
from csvcubed.utils.pandas import read_csv
from csvcubed.inputs import pandas_input_to_columnar_str, PandasDataTypes
from csvcubed.models.validationerror import ValidationError

from gssutils.csvcubedintegration.configloaders.jsonschemavalidation import (
    validate_dict_against_schema_url,
)
import gssutils.csvcubedintegration.configloaders.infojson1point1.mapcolumntocomponent as v1point1
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


def get_schema_errors(info_json: Path) -> List[JsonSchemaValidationError]:
    with open(info_json, "r") as f:
        info_json_contents = json.load(f)

    schema_errors = validate_dict_against_schema_url(
        info_json_contents,
        "https://raw.githubusercontent.com/GSS-Cogs/family-schemas/main/dataset-schema-1.1.0.json",
    )
    return schema_errors


def get_cube_from_info_json(
    info_json: Path, csv_path: Path, cube_id: Optional[str] = None
) -> Tuple[QbCube, List[ValidationError], List[JsonSchemaValidationError]]:
    """
    Generates a QbCube structure from an info.json input.
    :return: tuple of cube and json schema errors (if any)
    """

    with open(info_json, "r") as f:
        config = json.load(f)

    if cube_id is not None:
        config = _override_config_for_cube_id(config, cube_id)

    if config is None:
        raise Exception(f"Config not found for cube with id '{cube_id}'")

    return _from_info_json_dict(config, csv_path, info_json.parent.absolute())


def _override_config_for_cube_id(config: Dict, cube_id: str) -> Optional[dict]:
    """
    Apply cube config overrides contained inside the `cubes` dictionary to get the config for the given `cube_id`
    """
    # Need to do a deep-clone of the config to avoid side-effecs
    config = copy.deepcopy(config)

    info_json_id = config.get("id")
    if info_json_id is not None and info_json_id == cube_id:
        if "cubes" in config:
            del config["cubes"]

        return config
    elif "cubes" in config and cube_id in config["cubes"]:
        overrides = config["cubes"][cube_id]
        for k, v in overrides.items():
            config[k] = v

        return config
    else:
        return None


def _from_info_json_dict(
    config: Dict, csv_path: Path, info_json_parent_dir: Path
) -> QbCube:

    info_json_schema_url = "https://raw.githubusercontent.com/GSS-Cogs/family-schemas/main/dataset-schema-1.1.0.json"

    errors = validate_dict_against_schema_url(
        value=config, schema_url=info_json_schema_url
    )

    # Dimensions are always type str
    # This is necessary to stop pandas type assumptions altering outputs on the csv write,
    # by default a column of eg: ["04", "4"] would be assumed as numerical by pandas and
    # output as [4, 4]. In the context of a dimension 4 != 04
    dtypes = {
        column_label: str
        for column_label, column_config in config["transform"]["columns"].items()
        if column_config["type"] == "dimension"
    }
    data, validation_errors = read_csv(csv_path, dtype=dtypes)

    metadata = _metadata_from_dict(config)
    transform_section = config.get("transform", {})

    columns = _columns_from_info_json(
        transform_section.get("columns", []), data, info_json_parent_dir
    )
    uri_style = _uri_style_from_transform(transform_section)

    return Cube(metadata, data, columns, uri_style), errors, validation_errors


def _uri_style_from_transform(transform_section):
    if "csvcubed_uri_style" in transform_section:
        return URIStyle[transform_section["csvcubed_uri_style"]]
    return URIStyle.Standard


def _metadata_from_dict(config: Dict) -> "CatalogMetadata":
    publisher = get_with_func_or_none(
        config, "publisher", lambda p: str(GOV[uri_safe(p)])
    )
    theme_uris = [str(GDP.term(pathify(t))) for t in config.get("families", [])]
    dt_issued = (
        get_with_func_or_none(config, "published", parser.parse)
        or datetime.datetime.now()
    )
    landing_page_value = config.get("landingPage", [])

    return CatalogMetadata(
        title=get_from_dict_ensure_exists(config, "title"),
        summary=config.get("summary"),
        description=config.get("description"),
        creator_uri=publisher,
        publisher_uri=publisher,
        dataset_issued=dt_issued,
        theme_uris=theme_uris,
        keywords=config.get("keywords", []),
        landing_page_uris=landing_page_value
        if isinstance(landing_page_value, list)
        else [landing_page_value],
        license_uri=config.get("license"),
        public_contact_point_uri=config.get("contactUri"),
        uri_safe_identifier_override=get_from_dict_ensure_exists(config, "id"),
    )


def _columns_from_info_json(
    column_mappings: Dict[str, Any], data: pd.DataFrame, info_json_parent_dir: Path
) -> List[CsvColumn]:
    defined_columns: List[CsvColumn] = []

    column_titles_in_data: List[str] = [
        str(title) for title in data.columns  # type: ignore
    ]
    for col_title in column_titles_in_data:
        maybe_config = column_mappings.get(col_title)
        defined_columns.append(
            _get_column_for_metadata_config(
                col_title, maybe_config, data[col_title], info_json_parent_dir
            )
        )

    columns_missing_in_data = set(column_mappings.keys()) - set(column_titles_in_data)
    for col_title in columns_missing_in_data:
        config = column_mappings[col_title]
        defined_columns.append(
            _get_column_for_metadata_config(
                col_title, config, pd.Series([]), info_json_parent_dir
            )
        )

    return defined_columns


def _get_column_for_metadata_config(
    column_name: str,
    col_config: Optional[Union[dict, bool]],
    column_data: PandasDataTypes,
    info_json_parent_dir: Path,
) -> CsvColumn:
    if isinstance(col_config, dict):
        if col_config.get("type") is not None:
            return v1point1.map_column_to_qb_component(
                column_name, col_config, column_data, info_json_parent_dir
            )
        csv_safe_column_name = csvw_column_name_safe(column_name)

        maybe_dimension_uri = col_config.get("dimension")
        maybe_property_value_url = col_config.get("value")
        maybe_parent_uri = col_config.get("parent")
        maybe_description = col_config.get("description")
        maybe_label = col_config.get("label")
        maybe_attribute_uri = col_config.get("attribute")
        maybe_unit_uri = col_config.get("unit")
        maybe_measure_uri = col_config.get("measure")
        maybe_data_type = col_config.get("datatype")

        if maybe_dimension_uri is not None and maybe_property_value_url is not None:
            if maybe_dimension_uri == "http://purl.org/linked-data/cube#measureType":
                # multi-measure cube
                defined_measure_types: List[str] = col_config.get("types", [])
                if maybe_property_value_url is not None:
                    defined_measure_types = [
                        uritemplate.expand(
                            maybe_property_value_url, {csv_safe_column_name: d}
                        )
                        for d in defined_measure_types
                    ]

                if len(defined_measure_types) == 0:
                    raise Exception(
                        f"Property 'types' was not defined in measure types column '{column_name}'."
                    )

                measures = QbMultiMeasureDimension(
                    [ExistingQbMeasure(t) for t in defined_measure_types]
                )
                return QbColumn(column_name, measures, maybe_property_value_url)
            else:
                return QbColumn(
                    column_name,
                    ExistingQbDimension(maybe_dimension_uri),
                    maybe_property_value_url,
                )
        elif (
            maybe_parent_uri is not None
            or maybe_description is not None
            or maybe_label is not None
        ):
            label: str = column_name if maybe_label is None else maybe_label
            code_list = _get_code_list(
                label,
                col_config.get("codelist"),
                info_json_parent_dir,
                maybe_parent_uri,
                column_data,
                maybe_property_value_url,
            )
            new_dimension = NewQbDimension(
                label,
                description=maybe_description,
                parent_dimension_uri=maybe_parent_uri,
                source_uri=col_config.get("source"),
                code_list=code_list,
            )
            csv_column_value_url_template = (
                None
                if isinstance(code_list, CompositeQbCodeList)
                else maybe_property_value_url
            )
            return QbColumn(
                column_name,
                new_dimension,
                csv_column_value_url_template,
            )
        elif maybe_attribute_uri is not None and maybe_property_value_url is not None:
            if (
                maybe_attribute_uri
                == "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
            ):
                distinct_unit_uris = [
                    uritemplate.expand(
                        maybe_property_value_url, {csv_safe_column_name: u}
                    )
                    for u in set(pandas_input_to_columnar_str(column_data))
                ]
                dsd_component = QbMultiUnits(
                    [ExistingQbUnit(u) for u in distinct_unit_uris]
                )
            else:
                dsd_component = ExistingQbAttribute(maybe_attribute_uri)

            return QbColumn(column_name, dsd_component, maybe_property_value_url)
        elif maybe_unit_uri is not None and maybe_measure_uri is not None:
            measure_component = ExistingQbMeasure(maybe_measure_uri)
            unit_component = ExistingQbUnit(maybe_unit_uri)
            observation_value = QbSingleMeasureObservationValue(
                measure=measure_component,
                unit=unit_component,
                data_type=maybe_data_type or "decimal",
            )
            return QbColumn(column_name, observation_value)
        elif maybe_data_type is not None:
            return QbColumn(
                column_name, QbMultiMeasureObservationValue(maybe_data_type)
            )
        else:
            raise Exception(f"Unmatched column definition: {col_config}")
    elif isinstance(col_config, bool) and col_config:
        return SuppressedCsvColumn(column_name)
    else:
        # If not a known/expected type/value (or is a string), treat it as a dimension.
        maybe_description: Optional[str] = None
        if isinstance(col_config, str):
            maybe_description = col_config

        new_dimension = NewQbDimension.from_data(
            column_name, column_data, description=maybe_description
        )
        return QbColumn(column_name, new_dimension)


def _get_code_list(
    column_label: str,
    maybe_code_list: Optional[Union[bool, str]],
    info_json_parent_dir: Path,
    maybe_parent_uri: Optional[str],
    column_data: PandasDataTypes,
    maybe_property_value_url: Optional[str],
) -> Optional[QbCodeList]:
    is_date_time_code_list = (
        (
            maybe_code_list is None
            or (isinstance(maybe_code_list, bool) and maybe_code_list)
        )
        and maybe_parent_uri
        == "http://purl.org/linked-data/sdmx/2009/dimension#refPeriod"
        and maybe_property_value_url is not None
        and maybe_property_value_url.startswith("http://reference.data.gov.uk/id/")
    )

    if is_date_time_code_list:
        column_name_csvw_safe = csvw_column_name_safe(column_label)
        columnar_data = pandas_input_to_columnar_str(column_data)
        concepts = [
            DuplicatedQbConcept(
                existing_concept_uri=uritemplate.expand(
                    maybe_property_value_url, {column_name_csvw_safe: c}
                ),
                label=c,
            )
            for c in sorted(set(columnar_data))
        ]
        return CompositeQbCodeList(
            CatalogMetadata(column_label),
            concepts,
        )
    elif maybe_code_list is not None:
        if isinstance(maybe_code_list, str):
            return ExistingQbCodeList(maybe_code_list)
        elif isinstance(maybe_code_list, bool) and not maybe_code_list:
            return None
        else:
            raise Exception(f"Unexpected codelist value '{maybe_code_list}'")

    return NewQbCodeListInCsvW(
        info_json_parent_dir
        / "codelists"
        / f"{uri_safe(column_label)}.csv-metadata.json"
    )
