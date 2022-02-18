# Defining Measures Columns

> This document is part of a wider discussion on [Defining Columns in an info.json v1.1](./README.md).

**For use in multi-measure datasets only.**

A `measures` column is a column in a tidy multi-measure dataset which defines what is being measured/observed in a given observation-row. The measures can either be *new*ly created or *existing* resources defined elsewhere. However, **a single measure column cannot currently support a mix of existing and new measures**; you must only use *existing* measures **or** *new* measures in a given `measures` column.

## New Measures

Automatically defining a series of new measures from the values contained within the column:

```json
{
    "type": "measures"
}
```

## New Measures - Specified

Defining a series of new measures.

```json
{
    "type": "measures",
    "new": [
        {
            "label": "Mean Income"
        },
        {
            "label": "Median Income",
            "path": "median-income-path",
            "comment": "A description of what median income is. I cannot use Markdown or HTML here.",
            "isDefinedBy": "http://example.com/definitions/something-which-explains-what-this-measure-means.pdf"
        }
    ]
}
```

## Existing Measures

Defining the mapping to convert the measure column's text into the measure URIs.

```json
{
    "type": "measures",
    "value": "http://example.com/measures/{+column_name}"
}
```
