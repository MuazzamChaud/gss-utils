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

    1.) Get the _titles_ only from the csv
    2.) Use the title and column config (sub dict from info json "columns" field)
        to identify the appropriate column schema.
    3.) Use the column schemas to identify appropriate data types for 
        reading in the data.
    4.) Read in the data using those datatypes
    5.) Use the data & schema & column config to create the QbColumn objects.

    The ordering is critical, as 5 USES the data, said data must
    have been read in using data types as identified by 3 which is
    dependent on 2 and 1 (which has a limited csv read of its own - note I
    said LIMITED).

    If you try and do a single bulk read up front (a logical first instinct)
    you end up with correctly typed source data and pandas "best guess" typed
    code lists, that way likes madness.
    """

    metadata = _metadata_from_dict(config)
    transform_section = config.get("transform", {})

    # step 1
    column_titles_in_data = pd.read_csv(data_path, nrows=0).columns.tolist()
    column_mappings = transform_section.get("columns", [])

    # step 2
    column_schemas = {}
    for column_title in column_titles_in_data:
        maybe_config = column_mappings.get(column_title)
        column_schemas[column_title] = _get_column_schema(column_title, maybe_config)

    # step 3
    dtype_mapping = _get_dtypes_from_schemas(column_schemas)

    # step 4
    data, validation_errors = read_csv(data_path, dtype=dtype_mapping)

    # step 5
    qb_columns = get_qb_columns(column_mappings, column_schemas, data, info_json_parent_dir)

    uri_style = _uri_style_from_transform(transform_section)
    return Cube(metadata, data, qb_columns, uri_style), validation_errors


def _get_dtypes_from_schemas(column_schemas: Dict[str, schema.SchemaBaseClass]) -> Dict[str, str]:
    """
    Given a dict of: {<column titls>:<column dict from info_json>}

    Return a mapping of csvw spec datatypes to pandas primitive datatypes.
    The mapping is provided by ACCEPTED_DATATYPE_MAPPING from csvcubed itself.
    """

    dtypes = {}
    for column_title, column_schema in column_schemas.items():
        
        if hasattr(column_schema, "data_type"):
            dtype_str = column_schema["data_type"]
        elif isinstance(column_schema, schema.ObservationValue):
            dtype_str = "decimal"
        else:
            dtype_str = "string"

        # Note: always use the map even where we're mapping from say
        # "string" to "string", the mapping can potnetially change, the
        # logic calling the mapping shouldn't.
        dtypes[column_title] = ACCEPTED_DATATYPE_MAPPING[dtype_str]

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


def _get_column_schema(
    column_name: str,
    col_config: Optional[Union[dict, bool]],
) -> schema.SchemaBaseClass:
    """
    Using the fields in question, get the column schema
    """
    if isinstance(col_config, dict):
        if col_config.get("type") is not None:
            return v1point1.from_column_dict_to_schema_model(column_name, col_config)

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
                return schema.NewMeasures
            return schema.ExistingDimension
        elif (
            maybe_parent_uri is not None
            or maybe_description is not None
            or maybe_label is not None
        ):
            return schema.NewDimension
        elif maybe_attribute_uri is not None and maybe_property_value_url is not None:
            if (
                maybe_attribute_uri
                == "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
            ):
                return schema.NewUnits
            return schema.ExistingAttribute

        elif maybe_unit_uri is not None and maybe_measure_uri is not None:
            return schema.ObservationValue
        elif maybe_data_type is not None:
            return schema.ObservationValue
        else:
            raise Exception(f"Could not identify column schema for: {col_config}")

    elif isinstance(col_config, bool) and col_config:
        return col_config
    else:
        # If not a known/expected type/value (or is a string), treat it as a dimension.
        return schema.NewDimension


def get_qb_columns(
    column_mappings: Dict,
    column_schemas: Dict[str, schema.SchemaBaseClass], data: pd.DataFrame, info_json_parent_dir: Path
) -> List[CsvColumn]:
    """
    Use the schema and column config to create QbColumn classes representing all
    the columns (a) defined and (b) in the csv.

    --- Variables ---

    column_mappings: the sub dict from the info json defining a column,
    example of a single key:value pair:
    "Dim-0": {
                "type": "dimension",
                "new": {
                    "label": "Dim-0 Label",
                    "codelist": true
                }
            },

    column_schema: is a child of SchemaBaseClassas as provided by _get_column_schema
    
    data: pandas dataframe, for some QbComponents (some attributes and dimensions
    requiring codelists) we need the pd.Series of the column.

    info_json_parent_dir: required so we know where to putput any local codelists
    that are generated.
    """
    qb_columns: List[QbColumn] = []

    for column_name, col_config in column_mappings.items():
        column_schema = column_schemas[column_name]

        # Use data if the column has a data representation in the csv
        if column_name in data.columns.values:
            column_data: pd.Series = data[column_name]
        else:
            column_data: pd.Series = pd.Series([])

        # Scenario 1:
        # If we have an explicit type, we can use schema based constructors
        if col_config.get("type") is not None:
            populated_column_schema = column_schema.from_dict(col_config)
            
            if isinstance(populated_column_schema, schema.NewDimension):
                qb_column = QbColumn(column_name,
                        populated_column_schema.map_to_new_qb_dimension(column_name,
                        column_data, info_json_parent_dir))

            elif isinstance(populated_column_schema, schema.ExistingDimension):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_existing_qb_dimension())

            elif isinstance(populated_column_schema, schema.NewAttribute):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_new_qb_attribute(column_name, column_data))

            elif isinstance(populated_column_schema, schema.ExistingAttribute):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_existing_qb_attribute(column_data))

            elif isinstance(populated_column_schema, schema.NewUnits):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_qb_multi_units(column_data))

            elif isinstance(populated_column_schema, schema.ExistingUnits):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_qb_multi_units(column_data, column_name))

            elif isinstance(populated_column_schema, schema.NewMeasures):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_multi_measure_dimension(column_data))

            elif isinstance(populated_column_schema, schema.ExistingMeasures):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_multi_measure_dimension(column_name, column_data))
                  
            elif isinstance(populated_column_schema, schema.ObservationValue):
                qb_column = QbColumn(column_name, populated_column_schema.map_to_qb_observation())

            else:
                raise Exception(f"No mapping function for {populated_column_schema}")
                  
            qb_columns.append(qb_column)
            continue

        # Scenario 2:
        # when an explicit type is not porvided, we need to infer the correct
        # qb column type based on the input fields.
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

        if isinstance(column_schema, schema.NewMeasures):
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
                    f"Property 'types' was not defined in measure types column '{column_name} with config {col_config}'."
                )

            measures = QbMultiMeasureDimension(
                [ExistingQbMeasure(t) for t in defined_measure_types]
            )
            qb_columns.append(QbColumn(column_name, measures, maybe_property_value_url))

        elif isinstance(column_schema, schema.ExistingDimension):
            qb_columns.append(QbColumn(
                    column_name,
                    ExistingQbDimension(maybe_dimension_uri),
                    maybe_property_value_url,
                ))

        elif isinstance(column_schema, schema.NewDimension) and any([
            maybe_parent_uri is not None,
            maybe_description is not None,
            maybe_label is not None]):

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
            qb_columns.append(QbColumn(
                column_name,
                new_dimension,
                csv_column_value_url_template,
            ))

        elif isinstance(column_schema, schema.NewUnits):
            distinct_unit_uris = [
                    uritemplate.expand(
                        maybe_property_value_url, {csv_safe_column_name: u}
                    )
                    for u in set(pandas_input_to_columnar_str(column_data))
                ]
            multi_unit = QbMultiUnits(
                    [ExistingQbUnit(u) for u in distinct_unit_uris]
                )
            qb_columns.append(QbColumn(column_name, multi_unit, maybe_property_value_url))

        elif isinstance(column_schema, schema.ExistingAttribute):
            qb_columns.append(ExistingQbAttribute(maybe_attribute_uri))

        elif isinstance(column_schema, schema.ObservationValue):
            measure_component = ExistingQbMeasure(maybe_measure_uri)
            unit_component = ExistingQbUnit(maybe_unit_uri)
            observation_value = QbSingleMeasureObservationValue(
                measure=measure_component,
                unit=unit_component,
                data_type=maybe_data_type or "decimal",
            )
            qb_columns.append(QbColumn(column_name, observation_value))

        elif isinstance(col_config, bool) and col_config:
            qb_columns.append(QbColumn(
                column_name, SuppressedCsvColumn(column_name)
            ))

        elif isinstance(column_schema, schema.NewDimension):
            maybe_description: Optional[str] = None
            if isinstance(col_config, str):
                maybe_description = col_config

            label: str = column_name if maybe_label is None else maybe_label
            new_dimension = NewQbDimension.from_data(
                label, column_data, description=maybe_description
            )
            qb_columns.append(QbColumn(column_name, new_dimension))

        elif isinstance(column_schema, schema.NewAttribute):
            qb_columns.append(NewQbAttribute(
                label=column_name if maybe_label is None else maybe_label,
            ))

        else:
            raise Exception(f'Unable to crete QbColumn with {type(column_schema)}: {col_config}')

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
