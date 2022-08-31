"""
Mapping
-------

Map info.json V1.1 definitions to QB column components
"""
import copy
from typing import Union
from pathlib import Path

from csvcubed.models.cube import CompositeQbCodeList
from csvcubed.models.cube.qb.columns import QbColumn
from csvcubed.inputs import PandasDataTypes

import gssutils.csvcubedintegration.configloaders.infojson1point1.columnschema as schema


def map_column_to_qb_component(
    column_title: str, schema_mapping: schema.SchemaBaseClass, data: PandasDataTypes, info_json_parent_dir: Path
) -> QbColumn:
    """
    Takes an info.json v1.1 column mapping and, if valid,
    returns a :obj:`~csvcubed.models.cube.qb.components.datastructuredefinition.QbDataStructureDefinition`.
    """

    if isinstance(schema_mapping, schema.NewDimension):
        new_qb_dimension = schema_mapping.map_to_new_qb_dimension(
            column_title, data, info_json_parent_dir
        )
        uri_template = (
            None
            if isinstance(new_qb_dimension.code_list, CompositeQbCodeList)
            else schema_mapping.value
        )
        return QbColumn(
            column_title,
            new_qb_dimension,
            csv_column_uri_template=uri_template,
        )
    elif isinstance(schema_mapping, schema.ExistingDimension):
        return QbColumn(
            column_title,
            schema_mapping.map_to_existing_qb_dimension(),
            csv_column_uri_template=schema_mapping.value,
        )
    elif isinstance(schema_mapping, schema.NewAttribute):
        return QbColumn(
            column_title,
            schema_mapping.map_to_new_qb_attribute(column_title, data),
            csv_column_uri_template=schema_mapping.value,
        )
    elif isinstance(schema_mapping, schema.ExistingAttribute):
        return QbColumn(
            column_title,
            schema_mapping.map_to_existing_qb_attribute(data),
            csv_column_uri_template=schema_mapping.value,
        )
    elif isinstance(schema_mapping, schema.NewUnits):
        return QbColumn(column_title, schema_mapping.map_to_qb_multi_units(data))
    elif isinstance(schema_mapping, schema.ExistingUnits):
        return QbColumn(
            column_title,
            schema_mapping.map_to_qb_multi_units(column_title, data),
            csv_column_uri_template=schema_mapping.value,
        )
    elif isinstance(schema_mapping, schema.NewMeasures):
        return QbColumn(
            column_title, schema_mapping.map_to_multi_measure_dimension(data)
        )
    elif isinstance(schema_mapping, schema.ExistingMeasures):
        return QbColumn(
            column_title,
            schema_mapping.map_to_multi_measure_dimension(column_title, data),
            csv_column_uri_template=schema_mapping.value,
        )
    elif isinstance(schema_mapping, schema.ObservationValue):
        return QbColumn(column_title, schema_mapping.map_to_qb_observation())
    else:
        raise ValueError(f"Unmatched schema model type {schema_mapping}")


def from_column_dict_to_schema_model(
    column_title: str,
    column: dict,
) -> Union[
    schema.NewDimension,
    schema.ExistingDimension,
    schema.NewAttribute,
    schema.ExistingAttribute,
    schema.NewUnits,
    schema.ExistingUnits,
    schema.NewMeasures,
    schema.ExistingMeasures,
    schema.ObservationValue,
]:
    """
    N.B. when using the :method:`dict_fields_match_class` method, we need to ensure that we check for types with
    required properties *before* types without required properties.
    """
    column_type = column.get("type")
    column_without_type = copy.deepcopy(column)
    del column_without_type["type"]

    if column_type is None:
        raise ValueError("Type of column not specified.")
    elif column_type == "dimension":
        if schema.ExistingDimension.dict_fields_match_class(column_without_type):
            return schema.ExistingDimension
        elif schema.NewDimension.dict_fields_match_class(column_without_type):
            return schema.NewDimension
    elif column_type == "attribute":
        if schema.ExistingAttribute.dict_fields_match_class(column_without_type):
            return schema.ExistingAttribute
        elif schema.NewAttribute.dict_fields_match_class(column_without_type):
            return schema.NewAttribute
    elif column_type == "units":
        if schema.ExistingUnits.dict_fields_match_class(column_without_type):
            return schema.ExistingUnits
        elif schema.NewUnits.dict_fields_match_class(column_without_type):
            return schema.NewUnits
    elif column_type == "measures":
        if schema.ExistingMeasures.dict_fields_match_class(column_without_type):
            return schema.ExistingMeasures
        elif schema.NewMeasures.dict_fields_match_class(column_without_type):
            return schema.NewMeasures
    elif column_type == "observations":
        return schema.ObservationValue

    raise ValueError(
        f"Column '{column_title}' with type '{column_type}' could not be understood."
    )
