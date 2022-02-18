# Defining Attribute Columns

> This document is part of a wider discussion on [Defining Columns in an info.json v1.1](./README.md).

Unlike [dimensions](./DimensionColumns.md):

* attributes can point at [*literal values*](#attribute-literals) as well as *URI resources*.
* [Attributes can be *optional* by default](https://www.w3.org/TR/vocab-data-cube/#ic-6), i.e. you don't have to provide a value for every attribute in every observation-row. It is possible to define required attributes.

The rest of this document will provide some examples of attribute column definitions which you might find useful.

## New Attribute

Here we define a *new* attribute where:

* its label is the same as the CSV column's title
* all *attribute values* are inferred from the unique values in the column and have their own labelled URI resources created.

```json
{
    "type": "attribute"
}
```

### With Specific New Attribute Values

Use this where you want to create a *new* attribute with a hard-coded list of specific attribute values.

```json
{
    "type": "attribute",
    "new": {
        "newAttributeValues": [
            {
                "label": "Provisional"
            },
            {
                "label": "Final",
                "path": "some-path-for-final",
                "comment": "Description of what 'Final' means. I cannot use HTML or Markdown here.",
                "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-attribute-value-means.pdf"
            }
        ]
    }
}
```

It is also possible to define a *new* attribute which re-uses *existing* attribute values similar to [Existing Attribute With *Existing* Attribute Values](#with-existing-attribute-values).

## Existing Attribute

Here we re-use an *existing* attribute property (`http://gss-data.org.uk/def/trade/property/attribute/marker`).

### With *Existing* Attribute Values

How to re-use an *existing* attribute property and re-use *existing* attribute values at the same time.

```json
{
    "type": "attribute",
    "uri": "http://gss-data.org.uk/def/trade/property/attribute/marker",
    "value": "http://example.com/attribute-values/{+column_name}
}
```

**N.B. You must provide the `value` when defining attributes using existing attribute values**. This defines how the values in the column's cells are mapped into URIs pointing to *existing* attribute value resources. See [RFC 6570](https://datatracker.ietf.org/doc/html/rfc6570) for more information on the URI templating syntax used and [here](https://www.w3.org/TR/2015/REC-tabular-metadata-20151217/#uri-template-properties) for more information on their use within CSV-Ws.

### With *New* Attribute Values

An existing attribute definition can be extended with new attribute values found only in this dataset (and not in the externally defined attribute).

```json
{
    "type": "attribute",
    "uri": "http://gss-data.org.uk/def/trade/property/attribute/marker",
    "newAttributeValues": true
}
```

This example will automatically generate *new* attribute values from the unique values contained within the column. It is also possible to manually specify a curated list of *new* attribute values as in [New Attributes With Specific New Attribute Values](#with-specific-new-attribute-values).

## Required Attribute

It is possible to specify that it is *required* that all observation-rows have a value for an attribute. This can apply to both *new* and *existing* attribute definitions and only requires the addition of the `"isRequired": true` statement.

```json
{
    "type": "attribute",
    "uri": "http://gss-data.org.uk/def/trade/property/attribute/marker",
    "isRequired": true
}
```

## New Attribute - Everything Specified

Here we specify all of the properties it is possible to use against a new attribute.

```json
{
    "type": "attribute",
    "new": {
        "label": "This Attribute's Name",
        "path": "some-attribute-path",
        "comment": "I can describe the attribute is more detail here. I cannot use MarkDown or HTML.",
        "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-attribute-means.pdf",
        "subPropertyOf": "http://example.com/attribute/something-more-generic",
        "newAttributeValues": true
    }
}
```

* **the `path` represents the final part of the URI which identifies this attribute**. For example if all attributes are typically stored under `http://example.com/attributes/`, then this attribute would have a URI of `http://example.com/attributes/some-attribute-path`
* **the `subPropertyOf` represents a parent attribute property which is a more general representation of this attribute**. This attribute is a specialisation of the parent attribute.
* The `isDefinedBy` property provides the URL to a document which helps provide a human-friendly definition of this attribute.

## Attribute Literals

Attributes values are represented by default as resources with their own individual URIs. This makes sense where the attribute's data is catagorical, however it doesn't give us the flexiblity to add information about the observation which is continuous. For instance, we may want to assert that *this observation has a standard-error of 3.5 mm^2*. In general it does not make sense to generate a resource with a URI for the value `3.5`, so instead we allow you to define an attribute which holds literal values.

### New Attribute Literal

Here we define a new attribute which has literal values which  have the [double](https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/datatypes.html#double) datatype.

```json
{
    "type": "attribute",
    "new": {
        "label": "This Attribute's Name",
        "path": "some-attribute-path",
        "comment": "I can describe the attribute is more detail here. I cannot use MarkDown or HTML.",
        "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-attribute-means.pdf",
        "subPropertyOf": "http://example.com/attribute/something-more-generic",
        "literalValuesDataType": "double"        
    }
}
```

**N.B.**

* the `literalValuesDataType` property can take the value of any sensible [XSD data-type](https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/datatypes.html).
* you cannot specify both `newAttributeValues` and `literalValuesDataType` at the same time. If you do, an exception will result.

### Existing Attribute Literal

Here we declare that we will use an existing attribute (`http://example.com/attribute/some-attribute`) which has literal values which have the [double](https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/datatypes.html#double) datatype.

```json
{
    "type": "attribute",
    "uri": "http://example.com/attribute/some-attribute",
    "literalValuesDataType": "double"        
}
```

**N.B.**

* the `literalValuesDataType` property can take the value of any sensible [XSD data-type](https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/datatypes.html).
* you cannot specify both `newAttributeValues` and `literalValuesDataType` at the same time. If you do, an exception will result.
