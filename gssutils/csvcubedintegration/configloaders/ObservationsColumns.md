# Defining Observations Columns

> This document is part of a wider discussion on [Defining Columns in an info.json v1.1](./README.md).

## Existing Measure and Unit

```json
{
    "type": "observations",
    "measure": "http://gss-data.org.uk/def/measure/actual-income",
    "unit": "http://gss-data.org.uk/def/concept/measurement-units/gbp"
}
```

**N.B.**:

* **If your dataset has a [units column](./UnitsColumns.md), then it is possible to omit the `unit` definition here entirely.** However, the csvwlib tooling does not currently support the ability to provide duplicate observations with different units. It is only possible to define distinct units where the same dimensions are not repeated - i.e. a sub-set of the population was measured using one unit and another sub-set was measured using another unit.
* It is also possible to specify the `datatype` of the observation. This field accepts all of the [datatypes permitted in the CSV-W format](https://www.w3.org/TR/2015/REC-tabular-metadata-20151217/#built-in-datatypes). The default value is [double](https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/datatypes.html#double).

## Defining a New Measure

Here we define the suitable column definition for an observations column using an existing unit with a new measure.

```json
{
    "type": "observations",
    "datatype": "integer",
    "measure": {
        "label": "My New Measure",
        "path": "some-measure-path",
        "comment": "Description of my new measure. I can't put Markdown or HTML in here.",
        "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-measure-means.pdf"
    },
    "unit": "http://gss-data.org.uk/def/concept/measurement-units/gbp"
}
```

**N.B. the only require measure property is `label`**. All other properties are optional.

## Defining a New Unit

Here we define the suitable column definition for an observations column using an existing measure with a new unit.

```json
{
    "type": "observations",
    "measure": "http://gss-data.org.uk/def/measure/actual-income",
    "unit": {
        "label": "Kiloradians",
        "path": "my-new-unit-path",
        "comment": "Description of my new unit. I can't put Markdown or HTML in here.",
        "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-unit-means.pdf",
        "baseUnit": "http://qudt.org/vocab/unit/RAD",
        "baseUnitScalingFactor": 1000,
        "qudtQuantityKind": "http://qudt.org/vocab/quantitykind/Angle",
        "siBaseUnitConversionMultiplier": 1000
    }
}
```

See the [Defining New Units](./UnitsColumns.md#defining-new-units) section for more information on the unique properties that a new unit can have specified.

## Multi-Measure Observations

Multi-measure observations column definitions are simple where your dataset follows the standard shape and so has a `units` column as well as a `measures` column. In this case you do not need to specify a `measure` or `unit` property against the observation.

```json
{
    "type": "observations"
}
```

Of course you can also specify the `datatype` if desired.

## Missing, Suppressed or Redacted Observation Values

Data publishers often wish to avoid publishing particular observations, particularly where they reveal sensitive information or are redacted/suppressed to avoid disclosing data which could be used to identify an individual or business.

Our tooling allows you to create observations with missing values, **so long as an observation status/marker column is present which explains why the observed value is missing**. This marker column **must** either be an  [existing attribute](./AttributeColumns.md#existing-attribute) reusing the <http://purl.org/linked-data/sdmx/2009/attribute#obsStatus> URI or be a [new attribute](./AttributeColumns.md#new-attribute) which is a `subPropertyOf` <http://purl.org/linked-data/sdmx/2009/attribute#obsStatus>.
