"""
Info.json Loader
----------------

A loader for the info.json file format.
"""
import datetime
from typing import Dict, List, Tuple
from pathlib import Path
import json
import copy
import pandas as pd
import uritemplate
from dateutil import parser
from csvcubedmodels.rdf.namespaces import GOV, GDP
from csvcubed.models.cube import *
from csvcubed.models.validationerror import ValidationError
from csvcubed.utils.uri import csvw_column_name_safe, uri_safe
from csvcubed.utils.dict import get_from_dict_ensure_exists, get_with_func_or_none
from csvcubed.inputs import pandas_input_to_columnar_str, PandasDataTypes
from csvcubed.utils.pandas import read_csv
from csvcubed.models.cube.qb.components.constants import ACCEPTED_DATATYPE_MAPPING
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from gssutils.csvcubedintegration.configloaders.jsonschemavalidation import (
    validate_dict_against_schema_url,
)
import gssutils.csvcubedintegration.configloaders.infojson1point1.columnschema as schema
import gssutils.csvcubedintegration.configloaders.infojson1point1.mapcolumntocomponent as v1point1
from gssutils.utils import pathify


def get_cube_from_info_json(
    info_json_path: Path, data_path: Path, cube_id: Optional[str] = None
) -> Tuple[QbCube, List[ValidationError], List[JsonSchemaValidationError]]:
    """
    Generates a QbCube structure from an info.json input.
    :return: tuple of cube and json schema errors (if any)
    """
    
    with open(info_json_path, "r") as f:
        config = json.load(f)

    info_json_schema_url = "https://raw.githubusercontent.com/GSS-Cogs/family-schemas/main/dataset-schema-1.1.0.json"

    json_schema_validation_errors = validate_dict_against_schema_url(
        value=config, schema_url=info_json_schema_url
    )

    if cube_id is not None:
        config = _override_config_for_cube_id(config, cube_id)

    if config is None:
        raise Exception(f"Config not found for cube with id '{cube_id}'")
 
    cube, validation_errors = _from_info_json_dict(config, data_path, info_json_path.parent.absolute())
    return cube, validation_errors, json_schema_validation_errors


def _override_config_for_cube_id(config: dict, cube_id: str) -> Optional[dict]:
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
    config: Dict, data_path: Path, info_json_parent_dir: Path
) -> QbCube:
    """
    There is some convoluted but important ordering to be considered here,
    we need to:

    1.) Get the column titles only from the csv
    2.) Use the title and column config (sub dict from info json "columns" field)
        to identify the appropriate column schema.
    3.) Use the column schemas to identify appropriate data types for 
        reading in the data.
    4.) Read in the data using those datatypes
    5.) Use the (correctly type read) data & schema & column config to create the 
        QbColumn objects that inform the QbCube.

    The ordering is critical, as 5 USES the data, said data must
    have been read in using data types as identified by 3 which is
    dependent on 2 and 1 (which has a limited csv read of its own - note I
    said LIMITED, i.e header row only).

    If you try and do a single bulk read up front (a logical first instinct)
    you can end up with correctly typed source data and pandas "best guess"
    typed code lists.
    """

    metadata = _metadata_from_dict(config)
    transform_section = config.get("transform", {})

    # step 1
    column_titles_in_data = pd.read_csv(data_path, nrows=0).columns.tolist()
    column_mappings = transform_section.get("columns", [])

    columns_titles_not_in_data = [
        x for x in column_mappings if x not in column_titles_in_data
        ]

    all_columns = column_titles_in_data + columns_titles_not_in_data

    # step 2
    info_for_columns = []
    for column_title in all_columns:
        maybe_config = column_mappings.get(column_title)
        info_for_columns.append(
            schema.InfoForColumn(
                column_title, maybe_config
            ).with_column_schema()
        )

    # step 3
    dtype_mapping = _get_dtypes_from_schemas(info_for_columns)

    # step 4
    data, validation_errors = read_csv(data_path, dtype=dtype_mapping)

    # step 5
    qb_columns = get_qb_columns(info_for_columns, data, info_json_parent_dir)

    uri_style = _uri_style_from_transform(transform_section)
    return Cube(metadata, data, qb_columns, uri_style), validation_errors


def _get_dtypes_from_schemas(info_for_columns: List[schema.InfoForColumn]) -> Dict[str, str]:
    """
    Return a mapping of csvw spec datatypes to pandas primitive datatypes.
    The mapping is provided by ACCEPTED_DATATYPE_MAPPING from csvcubed itself.
    """

    dtypes = {}
    for column_info in info_for_columns:
        
        if column_info.schema_type is schema.ObservationValue:
            dtype_str = "decimal"
            if column_info.config:
                if "data_type" in column_info.config:
                    dtype_str = column_info.config["data_type"]
        elif column_info.config and "data_type" in column_info.config:
            dtype_str = column_info.config["data_type"]
        else:
            dtype_str = "string"

        # Note: always use the map even where we're mapping from say
        # "string" to "string", the mapping can potentially change.
        dtypes[column_info.name] = ACCEPTED_DATATYPE_MAPPING[dtype_str]

    return dtypes


def _uri_style_from_transform(transform_section):
    if "csvcubed_uri_style" in transform_section:
        return URIStyle[transform_section["csvcubed_uri_style"]]
    return URIStyle.Standard


def _metadata_from_dict(config: dict) -> "CatalogMetadata":
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
        landing_page_uris=landing_page_value if isinstance(landing_page_value, list) else [landing_page_value],
        license_uri=config.get("license"),
        public_contact_point_uri=config.get("contactUri"),
        uri_safe_identifier_override=get_from_dict_ensure_exists(config, "id"),
    )

def get_qb_columns(
    info_for_columns: List[schema.InfoForColumn], data: pd.DataFrame, info_json_parent_dir: Path
) -> List[CsvColumn]:
    """
    Use the schema and column config to create QbColumn classes representing all
    the columns (a) defined and (b) in the csv.
    """
    qb_columns: List[QbColumn] = []
    
    for column_info in info_for_columns:

        # Use data if the column has a data representation in the csv
        if column_info.name in data.columns.values:
            column_data: pd.Series = data[column_info.name]
        else:
            column_data: pd.Series = pd.Series([])

        # Scenario 1: QbColumn by convention
        if column_info.config is None and column_info.schema_type is schema.NewDimension:
            qb_columns.append(QbColumn(
                column_info.name,
                NewQbDimension.from_data(column_info.name, column_data))
            )
            continue

        # Scenario 2: QbColumn is explictly declared by type
        if column_info.config.get("type") is not None:
            qb_column = v1point1.map_column_to_qb_component(
                column_info.name, column_info.instantiate_schema(),
                column_data, info_json_parent_dir
            )

            qb_columns.append(qb_column)
            continue

        # Scenario 3: neither of the above, legacy approach so
        # we apply some conditionals to instantiate with required
        # arguments.
        csv_safe_column_name = csvw_column_name_safe(column_info.column_name)

        if column_info.schema_type is schema.NewMeasures:
            defined_measure_types: List[str] = column_info.config.get("types", [])
            if column_info.maybe_property_value_url is not None:
                defined_measure_types = [
                    uritemplate.expand(
                        column_info.maybe_property_value_url, {csv_safe_column_name: d}
                    )
                    for d in defined_measure_types
                ]

            if len(defined_measure_types) == 0:
                raise Exception(
                    f"Property 'types' was not defined in measure types column '{column_info.name} with config {column_info.config}'."
                )

            measures = QbMultiMeasureDimension(
                [ExistingQbMeasure(t) for t in defined_measure_types]
            )
            qb_columns.append(QbColumn(column_info.name, measures, column_info.maybe_property_value_url))

        elif column_info.schema_type is schema.ExistingDimension:
            qb_columns.append(QbColumn(
                    column_info.name,
                    ExistingQbDimension(column_info.maybe_dimension_uri),
                    column_info.maybe_property_value_url,
                ))

        elif column_info.schema_type is schema.NewDimension and any([
            column_info.maybe_parent_uri is not None,
            column_info.maybe_description is not None,
            column_info.maybe_label is not None]):

            label: str = column_info.name if column_info.maybe_label is None else column_info.maybe_label

            code_list = _get_code_list(
                label,
                column_info.config.get("codelist"),
                info_json_parent_dir,
                column_info.maybe_parent_uri,
                column_data,
                column_info.maybe_property_value_url,
            )
            new_dimension = NewQbDimension(
                label,
                description=maybe_description,
                parent_dimension_uri=column_info.maybe_parent_uri,
                source_uri=column_info.config.get("source"),
                code_list=code_list,
            )
            csv_column_value_url_template = (
                None
                if isinstance(code_list, CompositeQbCodeList)
                else column_info.maybe_property_value_url
            )
            qb_columns.append(QbColumn(
                column_info.name,
                new_dimension,
                csv_column_value_url_template,
            ))

        elif column_info.schema_type is schema.ExistingUnits:
            distinct_unit_uris = [
                    uritemplate.expand(
                        column_info.maybe_property_value_url, {csv_safe_column_name: u}
                    )
                    for u in set(pandas_input_to_columnar_str(column_data))
                ]
            dsd_component = QbMultiUnits(
                    [ExistingQbUnit(u) for u in distinct_unit_uris]
                )
            qb_columns.append(QbColumn(column_info.name, dsd_component, column_info.maybe_property_value_url))

        elif column_info.schema_type is schema.NewUnits:
            multi_unit = schema.NewUnits.from_dict(column_info.config).map_to_qb_multi_units(column_data)
            qb_columns.append(QbColumn(column_info.name, multi_unit, column_info.maybe_property_value_url))

        elif column_info.schema_type is schema.ExistingAttribute:
            qb_columns.append(QbColumn(
                column_info.name,
                ExistingQbAttribute(column_info.maybe_attribute_uri),
                column_info.maybe_property_value_url)
                )

        # schema.ObservationValue with a single measure
        elif all([
            column_info.schema_type is schema.ObservationValue,
            column_info.maybe_unit_uri is not None,
            column_info.maybe_measure_uri is not None
            ]):
            measure_component = ExistingQbMeasure(column_info.maybe_measure_uri)
            unit_component = ExistingQbUnit(column_info.maybe_unit_uri)
            observation_value = QbSingleMeasureObservationValue(
                measure=measure_component,
                unit=unit_component,
                data_type=column_info.maybe_data_type or "decimal",
            )
            qb_columns.append(QbColumn(column_info.name, observation_value))

        # schema.ObservationValue with multi measures
        elif all([
            column_info.schema_type is schema.ObservationValue,
            column_info.maybe_data_type is not None]):
                qb_columns.append(QbColumn(
                    column_info.name, QbMultiMeasureObservationValue(column_info.maybe_data_type)
                ))

        elif column_info.schema_type is  bool and column_info.config:
            qb_columns.append(QbColumn(
                column_info.name, SuppressedCsvColumn(column_info.name)
            ))

        elif column_info.schema_type is schema.NewDimension:
            maybe_description: Optional[str] = None
            if isinstance(column_info.config, str):
                maybe_description = column_info.config

            label: str = column_info.name if column_info.maybe_label is None else column_info.maybe_label
            new_dimension = NewQbDimension.from_data(
                label, column_data, description=maybe_description
            )
            qb_columns.append(QbColumn(column_info.name, new_dimension))

        elif column_info.schema_type is schema.NewAttribute:
            qb_columns.append(NewQbAttribute(
                label=column_info.name if column_info.maybe_label is None else column_info.maybe_label,
            ))

        else:
            raise Exception(f'Unable to create QbColumn with "{column_info.name}" : {column_info.schema_type} : {column_info.config}')

    return qb_columns


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
