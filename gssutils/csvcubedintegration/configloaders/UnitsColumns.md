# Defining Units Columns

> This document is part of a wider discussion on [Defining Columns in an info.json v1.1](./README.md).

For use where there is more than one unit in use across the dataset. **If there is only one unit for the whole dataset** then the *unit* should be specified within the *observations* column definition.

This is a *derived type* roughly equivalent to an *attribute* column using the existing `http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure` property.

The units specified in the column can either be *new*ly created or *existing* resources defined elsewhere. However, **a single units column cannot currently support a mix of existing and new units**; you must only use *existing* units **or** *new* units in a given `units` column.

## New Units

Automatically defining a series of new units from the values contained within the column:

```json
{
    "type": "units"
}
```

## New Units - Specified

Defining a series of new units.

```json
{
    "type": "units",
    "new": [
        {
            "label": "Kilo-degrees"
        },
        {
            "label": "Kilo-radians",
            "path": "kilo-radians-path",
            "comment": "A description of what kilo-radians are. I cannot use Markdown or HTML here.",
            "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-unit-means.pdf",
            "baseUnit": "http://qudt.org/vocab/unit/RAD",
            "baseUnitScalingFactor": 1000,
            "qudtQuantityKind": "http://qudt.org/vocab/quantitykind/Angle",
            "siBaseUnitConversionMultiplier": 1000
        }
    ]
}
```

See the [Defining New Units](#defining-new-units) section below for more information on the unique properties that a new unit can have specified.

## Existing Units

Defining the mapping to convert the units column's text into the units URIs.

```json
{
    "type": "measures",
    "value": "http://example.com/measures/{+column_name}"
}
```

## Defining New Units

When defining new units, there are an unusually large number of properties present. This is due to the fact that it is useful to be able to relate units back to other units using conversion factors to enable automated systems to compare data recorded in different (but comparable) units.

```json
{
    "label": "Kilo-radians",
    "path": "kilo-radians-path",
    "comment": "A description of what kilo-radians are. I cannot use Markdown or HTML here.",
    "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-unit-means.pdf",
    "baseUnit": "http://qudt.org/vocab/unit/RAD",
    "baseUnitScalingFactor": 1000,
    "qudtQuantityKind": "http://qudt.org/vocab/quantitykind/Angle",
    "siBaseUnitConversionMultiplier": 1000
}
```

* The only required `unit` property is `label`, all other are optional.
* `baseUnit` and `baseUnitScalingFactor` help define how this unit relates to an existing unit. Both properties must be provided together.
* `qudtQuantityKind` and `siBaseUnitConversionMultiplier` help define how the unit relates to the qudt system of [quantityKind](http://www.qudt.org/doc/DOC_VOCAB-QUANTITY-KINDS.html#Instances)s and hence defines the relationship between this unit and all other units within the same *quantityKind*. Both properties must be provided together.
