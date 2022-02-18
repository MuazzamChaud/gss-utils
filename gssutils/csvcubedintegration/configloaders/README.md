# Defining Columns in an info.json v1.1

This document will focus on how to write column definitions in an info.json v1.1 document. It assumes knowledge of JSON as well as a general understanding of the following statistical concepts relevant to data cubes:

* [dimensions](https://fmrwiki.sdmxcloud.org/Dimension)
* [attributes](https://fmrwiki.sdmxcloud.org/Attribute)
* [measures](https://fmrwiki.sdmxcloud.org/Measure)
* [observations](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Beginners:Statistical_concept_-_Observation)

## JSON Schema

The schema defines what is permitted inside an info.json v1.1 file and can be found [inside the GSS-Cogs/family-schemas](https://github.com/GSS-Cogs/family-schemas/blob/main/dataset-schema-1.1.0.json) repository.

It is possible to use the JSON schema to provide both validation and contextual hints to help you when you write your info.json files. This is a powerful piece of functionality which makes it easier to get your configuration files right before you try to combine the file with CSV data. It is therefore **strongly recommended** that you use a text editor which is able to validate JSON documents against schemas and provide contextual hints; the current recommended tool for this is [Visual Studio Code](https://code.visualstudio.com/).

**To enable validation and intellisense/contextual hints, you must start all info.json v1.1 documents with the following `$schema` declaration:**

```json
{
    "$schema": "http://gss-cogs.github.io/family-schemas/dataset-schema-1.1.0.json",
    ...
}
```

For a more complete template to use in your own info.json documents see [below](#basic-template).

## Components

> Every *qb cube* has a *data structure definition*.
>
> The *data structure definition* defines all of the cube's components, i.e. its dimensions, attributes and measures.
>
> Each info.json *column definition* describes how the column and its data fit into the cube's *data structure definition*.

You may have noticed that we have defined column types like `dimension` and `observations` without much explaination. Each of these types roughly maps to one or more parts of a *qb data structure definition*. The *data structure definition* of a *qb cube* describes the cube's structure and provides hints to applications (like PMD) as to how the data should be displayed and interpreted as well as how it can be filtered.

There are three types of qb/SDMX [component](https://fmrwiki.sdmxcloud.org/Component):

* [dimensions](https://fmrwiki.sdmxcloud.org/Dimension)
* [attributes](https://fmrwiki.sdmxcloud.org/Attribute)
* [measures](https://fmrwiki.sdmxcloud.org/Measure)

The info.json v1.1 schema has five types of column definition:

* *dimension*
* *attribute*
* *units*
* *measures*
* *observations*

Clearly we have a larger number of column definition types than there are *qb components*. This is because we've started to add some *derived types* which help make the job of a *Data Manager* easier by bridging the gap between the *qb* specification and the shapes of data that we accept. It's likely that we'll add new *derived types* in the future to make it easier to deal with oft-used dimensions like *DateTime Period* and *ONS Geography*.

### New vs. Existing

> A *new* column definition creates a new unit, measure, dimension or attribute resource locally to the dataset.
>
> An *existing* column definition re-uses an existing unit, measure, dimension or attribute resource that has been defined elsewhere.

It's important to grasp what we mean when we talk about a *new* column versus an *existing* column definition. *New* means that we're creating a new resource which is local to this dataset and *should not* be re-used in other datasets. *Existing* means that we're re-using an existing resource which has been defined somewhere else.

There's a tension here in our work that could probably use a bit of discussion. We're attempting to develop tools which help people develop and publish *linked data*, i.e. data that is linked together by the structural definitions that they have in common. If we're defining a *new* dimension that has already been defined elsewhere, we're getting further away from the goal of linking all of our datasets together. On the other hand, it is often difficult to decide whether and where the *new* dimension you're defining has already been defined, and this difficulty can make it frustrating and time-consuming to publish data. We know it's going to be difficult and time-consuming to produce *perfectly* linked data, so each dataset *can* (this does not mean *should*) start out with all dimensions, attributes, code-lists, measures and units defined locally to make it easier to publish data in the standardised qb format. Once the data has been published, we can incrementally improve it by using *existing* resources to make the data better linked as time goes on. Hopefully, once data producers become familiar with this process, they will start to design their dataset so that they use common/harmonised definitions from the very beginning, making the later job of data linkage much easier.

At the current point in time, it is hoped that *Data Engineers* will be able to produce a dataset which primarily defines *new* resources (except where it is easy to re-use *existing* resources e.g. units), and then it will be the *Data Manager*'s job to decide how the dataset can be modified and/or annotated such that we're using as many *existing* resources as possible so that the data links into the wider context relevant to the dataset's family/sector.

## Column Definitions

Column definitions form the key part of any transformation from a tidy CSV to a CSV-qb. They provide the metadata which describes what each CSV column represents and how it relates to existing (reusable) linked-data definitions.

The info.json schema requires that column definitions are defined inside the `transform.columns` object inside the document.

```json
{
    ...
    "transform": {
        "columns": {
            // Column definitions go here.
        }
    },
    ...
}
```

For each column in your input CSV, you should create a new column mapping inside `transform.columns`:

```json
"Column Title inside CSV": {
    // Definition of the column goes in here.
}
```

### Examples

This section provides an example of a quick approach to defining column mappings in an info.json file. All column definitions that we write will create *new* resources without much consideration of how we might re-use *existing* resources. We will also dispense with all configurability and only give the bare-bones structure necessary to get a valid CSV-qb when passed to [infojson2csvqb](../infojson2csvqb/README.md).  

#### **Single-Measure Dataset**

Consider the following table of data contained in a CSV file. We will define the column mappings necessary to transform this data into a valid CSV-qb.

| Town         | Year | Average Income | Marker      |
|:-------------|:-----|:--------------:|:------------|
| Chocster     | 2019 |     20,554     | Final       |
| Lemonton     | 2019 |     23,192     | Final       |
| Chiply       | 2019 |     18,612     | Final       |
| Biscuitburgh | 2019 |     22,745     | Final       |
| Chocster     | 2020 |     20,751     | Provisional |
| Lemonton     | 2020 |     24,198     | Provisional |
| Chiply       | 2020 |     19,618     | Provisional |
| Biscuitburgh | 2020 |     22,075     | Provisional |

The first step is to identify the types of each columns in the dataset:

* We note that `Town` and `Year` help partition up the dataset and identify which sub-set of the population is being measured. They are therefore `dimension` type columns.
* We see that the `Average Income` column contains the measured/observed values and so represents an `observations` type column.
* The `Marker` column represents data describing some state about the *observed value itself* and does not identify any subset of the dataset's population. This is therefore an `attribute` type column.

| Column Title   | Column Type  |
|:---------------|:-------------|
| Town           | dimension    |
| Year           | dimension    |
| Average Income | observations |
| Marker         | attribute    |

We then define JSON mappings for each column, specifying only their type at this point:

```json
{
    "Town": {
        "type": "dimension"
    },
    "Year": {
        "type": "dimension"
    },
    "Average Income": {
        "type": "observations"
    },
    "Marker": {
        "type": "attribute"
    }
}
```

We know that each observation must have a `measure` and a `unit`, however, we haven't provided this information anywhere just yet. In a single-measure dataset the measure and unit should be specified against the `observations` column. To keep things simple, we will define a new unit called *Nomland Pounds* and a new measure called *Income*:

```json
"Average Income": {
    "type": "observations",
    "measure": {
        "label": "Income"
    },
    "unit": {
        "label": "Nomland Pounds"
    }
}
```

For commonly used measures and units, it is also possible to directly specify the *existing* measure or unit that you wish to use, e.g.

```json
"Average Income": {
    "type": "observations",
    "measure": "http://gss-data.org.uk/def/measure/actual-income",
    "unit": "http://gss-data.org.uk/def/concept/measurement-units/nomland-pounds"
}
```

Putting all of this together, we end up with the following column definitions which are sufficient to generate a valid CSV-qb:

```json
{
    ...
    "transform": {
        "columns": {
            "Town": {
                "type": "dimension"
            },
            "Year": {
                "type": "dimension"
            },
            "Average Income": {
                "type": "observations",
                "measure": {
                    "label": "Income"
                },
                "unit": {
                    "label": "Nomland Pounds"
                }
            },
            "Marker": {
                "type": "attribute"
            }
        }
    },
    ...
}
```

#### **Multi-Measure Dataset**

Multi-measure datasets are similar to single-measure datasets, with the primary difference being how we specify units and measures. The only data-shape currently supported when generating multi-measure datasets is to define `measures` and `units` columns which specify the measure and unit for a given observation-row.

Consider the following simplified table of data contained in a CSV file.

| Town     | Measure    | Unit         | Value  |
|:---------|:-----------|:-------------|:------:|
| Chocster | Size       | Square Miles |  20.7  |
| Chocster | Population | People       | 14,980 |
| Lemonton | Size       | Square Miles |  14.3  |
| Lemonton | Population | People       | 26,740 |

Once again, we start by deciding the types of columns we have. This example is similar to the single-measure dataset, however the `Measure` column has a special type called `measures` and the `Unit` column has a special type called `units`.

| Column Title | Column Type  |
|:-------------|:-------------|
| Town         | dimension    |
| Measure      | measures     |
| Unit         | units        |
| Value        | observations |

Given that each row has its own unit and measure defined by the `units` and `measures` type columns, we no longer need to specify the unit or measure against the observation; doing so would lead to an error due to conflicting information.

This leads to the following bare-boned JSON which would generate a valid CSV-qb for this dataset:

```json
{
    ...
    "transform": {
        "columns": {
            "Town": {
                "type": "dimension"
            },
            "Measure": {
                "type": "measures"
            },
            "Unit": {
                "type": "units"
            },
            "Value": {
                "type": "observations"
            }
        }
    },
    ...
}
```

### Advanced Definitions

For a more thorough review of defining column mappings, see the following documents:

* [Defining Dimension Columns](./DimensionColumns.md)
* [Defining Attribute Columns](./AttributeColumns.md)
* [Defining Measures Columns](./MeasuresColumns.md)
* [Defining Units Columns](./UnitsColumns.md)
* [Defining Observations Columns](./ObservationsColumns.md)

This advanced documentation is primarily aimed at *Data Managers* but may be of use to curious *Data Engineers*.

## Use of the info.json v1.0 Syntax

Whilst v1.1 supports all v1.0 syntax and only **adds new functionality**, it is recommended that you avoid the use of v1.0 syntax and proceed with the more precise and better documented v1.1 syntax.

The best way to ensure that you're using v1.1 syntax is to ensure that your column definitions contain the `type` property, for example:

```JSON
{
    "type": "dimension",
    "new": {
        "label": "Some New Dimension",
        "codelist": false
    }
}
```

If your columns don't include the `type` property, then you are using the old info.json V1.0 syntax.

## Basic Template

The following stands as a minimal template for an info.json which you can use as a starting point for your own files. Note that only one column definiton has been written for demonstration purposes.

```json
{
    "$schema": "http://gss-cogs.github.io/family-schemas/dataset-schema-1.1.0.json",
    "title": "Some Dataset",
    "id": "some-dataset",
    "publisher": "Office for National Statistics",
    "families": [],
    "transform": {
        "columns": {
            "A Column Title Present in the CSV": {
                "type": "dimension"
            }
        },
        "airtable": "rec0000000000000000"
    }
}
```
