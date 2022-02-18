# Generating a CSV-qb from an info.json

This page will discuss how it is possible to use the `infojson2csvqb` command line application to convert a tidy-data CSV into qb-flavoured CSV-W files. 

## Quick Start

Run the following commands in order and ensure you get no errors:

```bash
echo "export PATH=\"$(echo ~/.local/bin):\$PATH\"" >> ~/.bash_profile
python3 -m pip install --user -e 'git+https://github.com/GSS-Cogs/gss-utils.git#egg=gssutils'
```

**Now close your terminal and open a new one.**

``` bash
infojson2csvqb build data.csv --config info.json  # N.B. Must refer to whatever you have called your Tidy CSV file and info.json
```

You should see an `./out` directory has been created containing the relevant data cube and code-list CSV-Ws which are free of any PMD-specific annotations.

## FAQ

> Can I see the RDF that will be uploaded to PMD by Jenkins?

No, we don't currently have any local processes which can convert the CSV-W directly into RDF that would be acceptable to PMD. The CSV-Ws need to be passed through Jenkins.

> How does this tool fit into the wider data pipeline?

This tools sits firmly in the middle of the pipeline. It follows the generation of a tidy-data CSV by a Data Engineer, and is run on the outputs of said process. After `infojson2csvqb` has been run, the CSV-Ws generated are augmented with PMD-specific annotations and shaped into something more performant for the PMD environment.

This tool is, however, designed to be used in a manual fashion by Data Managers to test the generation of CSV-Ws and aims to provided a more guided approach towards generating valid `CSV-qb`s.

> Can you help me figure out how to write an info.json file?

Not just yet, but hopefully at some point we'll have some sensible documentation on it somewhere.

## Installation

The `infojson2csvqb` command line interface is part of the [gss-utils](https://github.com/GSS-Cogs/gss-utils) python package and as such is available inside the [gsscogs/databaker](https://hub.docker.com/r/gsscogs/databaker) docker image. There are therefore two approaches to installing the `infojson2csvqb` tool, installing via `pip` or installation via `docker`.

### Installing with `pip`

First start by ensuring that your `~/.bash_profile` (or `~/.zshenv` if you're using ZSH) file adds your local python bin directory to the `PATH` variable:

```bash
echo "export PATH=\"$(echo ~/.local/bin):\$PATH\"" >> ~/.bash_profile
```

Then run the following command to install the `gssutils` package for your given user. This will make the `infojson2csvqb` command accessible anywhere for your user.

```bash
python3 -m pip install --user -e 'git+https://github.com/GSS-Cogs/gss-utils.git#egg=gssutils'
```

Next, close your terminal session, and open another one. You should now be able to make a call to the tool:

```bash
$ infojson2csvqb --help

Usage: infojson2csvqb [OPTIONS] COMMAND [ARGS]...
...
```

### Installing with `docker`

**Start by pulling the latest image**. If you ever need to update the tool, pulling the image again is all that you need to do.

```bash
docker pull gsscogs/databaker
```

You should now be able to run the `infojson2csvqb` command:

```bash
$ docker run --rm -v $(pwd):/workspace -w /workspace gsscogs/databaker infojson2csvqb --help

Usage: infojson2csvqb [OPTIONS] COMMAND [ARGS]...
...
```

Note the crucial `-v $(pwd):/workspace` part of the command. This mounts your current working directory inside the docker container at `/workspace`. This means you can only run `infojson2csvqb` against files located **within** the current working directory (and any sub-folders).

From hereon in, this documentation will assume that `gss-utils` has been installed using the `pip` method, however any of the commands can also be run via the docker method by replacing `infojson2csvqb` in the command with the docker alternative,

```bash
docker run --rm -v $(pwd):/workspace -w /workspace gsscogs/databaker infojson2csvqb
```

## Usage

### Help

```bash
$ infojson2csvqb --help

Usage: infojson2csvqb [OPTIONS] COMMAND [ARGS]...

  infojson2csvqb - a tool to generate qb-flavoured CSV-W cubes from COGS-style
  info.json files.

Options:
  -h, --help  Show this message and exit.

Commands:
  build  Build a qb-flavoured CSV-W from a tidy CSV.
```

### Build Command

```bash
$ infojson2csvqb build --help
Usage: infojson2csvqb build [OPTIONS] TIDY_CSV_PATH

  Build a qb-flavoured CSV-W from a tidy CSV.

Options:
  -c, --config CONFIG_PATH        Location of the info.json file containing
                                  the QB column mapping definitions.
                                  [required]
  -m, --catalog-metadata CATALOG_METADATA_PATH
                                  Location of a JSON file containing the
                                  Catalog Metadata for this qube. If present,
                                  this overrides any configuration found in
                                  the info.json.
  -o, --out OUT_DIR               Location of the CSV-W outputs.  [default:
                                  out]
  --fail-when-validation-error / --ignore-validation-errors
                                  Fail when validation errors occur or ignore
                                  validation errors and continue generating a
                                  CSV-W.  [default: fail-when-validation-
                                  error]
  --validation-errors-to-file     Save validation errors to an `validation-
                                  errors.json` file in the output directory.
                                  [default: False]
  -h, --help                      Show this message and exit.
```

The `infojson2csvqb build` command accepts one argument, `TIDY_CSV_PATH`, the location of the CSV containing tidydata. It is **vital** that your CSV contains tidy data which is structured in one of the **standard data shapes** accepted by the `csvcubed` library.

The command also expects the `--config` option. This should be the location of an `info.json` file which contains column definitions for the data contained in `TIDY_CSV_PATH`.

```bash
$ infojson2csvqb build data.csv --config info.json
CSV: /Users/user/dataset/data.csv
info.json: /Users/user/dataset/info.json
Creating output directory /Users/user/dataset/out
Build Complete
```

You will notice that the command has automatically assumed that its output files will be placed in the `./out` directory, which it has automatically created. This directory can be configured using the `--out` option.

The output files from this command are:

```bash
$ tree out 
out
├── ons-international-trade-in-services-by-subnational-areas-of-the-uk.csv
├── ons-international-trade-in-services-by-subnational-areas-of-the-uk.csv-metadata.json
├── undefined-column.csv
├── undefined-column.csv-metadata.json
└── undefined-column.table.json
```

The main dataset is contained inside the `ons-international-trade-in-services-by-subnational-areas-of-the-uk.csv` file and its associated JSON metadata file. This forms the main CSV-W. The name of the file is derived from the `id` or `title` fields inside the `info.json` file.

```json
{
    "id": "ons-international-trade-in-services-by-subnational-areas-of-the-uk",
    "title": "International trade in services by subnational areas of the UK",
    ...
}
```

We also see three files with the name `undefined-column`. These are definitions for a code-list which has been automatically generated from a column named `Undefined Column` in the tidy CSV input. All three files are vital to the definition of the code-list.

All locally-defined code-lists will have corresponding files declared in the `out` directory. Code-lists which are defined externally to the dataset will not be present even if they are referenced in the `info.json` file.

#### Catalog Metadata (from a scraper)

You may optionally pass the `--catalog-metadata` option providing the location of a JSON file containing metadata derived from a [scraper](../../scrape.py) using the `as_csvqb_catalog_metadata` function.

**N.B. the catalog metadata overrides the corresponding metadata specified in an info.json file.** It allows us to provide more specific overriding metadata which the scraper has acquired from a publisher's website.

The metadata is deserialised into a [qb CatalogMetadata](https://github.com/GSS-Cogs/csvwlib/blob/main/csvcubed/csvcubed/models/cube/qb/catalog.py) object. At the time of writing, an example of the currently acceptable metadata would be:

```json
{
    "title": "Some Dataset",
    "uri_safe_identifier_override": "some-dataset",
    "summary": "Some catalog item summary",
    "description": "Some catalog item description",
    "creator_uri": "http://some-creator-uri",
    "publisher_uri": "http://some-publisher-uri",
    "landing_page_uris": [
      "http://some-landing-page-uri"
    ],
    "theme_uris": [
        "http://some-theme-uri"
    ],
    "keywords": [
        "Some key word"
    ],
    "dataset_issued": "2010-01-01T01:01:01.000001",
    "dataset_modified": "2010-01-01T02:01:01.000001",
    "license_uri": "http://some-license-uri",
    "public_contact_point_uri": "mailto:somecontactpoint@ons.gov.uk"
}
```

#### Validation Errors

Validation errors occur when some aspect of your cube's definition is not correct. This could be because of:

* missing some necessary configuration,
* providing conflicting metadata,
* some of the data being invalid.

```bash
$ infojson2csvqb build data.csv --config info.json
CSV: /Users/user/dataset/data.csv
info.json: /Users/user/dataset/info.json
Creating output directory /Users/user/dataset/out
Validation Error: Found neither QbObservationValue.unit nor QbMultiUnits defined. One of these must be defined.
```

The above validation error warns that the dataset in question has no unit defined for the observations.

##### Writing Validation Errors to File

Sometimes you might want to write the validation errors to file. This functionality is important in the Jenkins pipeline where it's useful to output a file as a build artifact to make it easy to see exactly what went wrong.

```bash
$ infojson2csvqb build data.csv --config info.json --validation-errors-to-file
CSV: /Users/user/dataset/data.csv
info.json: /Users/user/dataset/info.json
Creating output directory /Users/user/dataset/out
Validation Error: Found neither QbObservationValue.unit nor QbMultiUnits defined. One of these must be defined.
```

The corresponding validation error file (in `./out/validation-errors.json`) will look something like this:

```json
[
    {
        "message": "Found neither QbObservationValue.unit nor QbMultiUnits defined. One of these must be defined.",
        "component_one": "QbObservationValue.unit",
        "component_two": "QbMultiUnits",
        "additional_explanation": null
    }
] 
```

##### Overriding Validation Errors

It is possible to override errors in validation and to continue attempting to generate a CSV-W.

**N.B. Deciding to override validation errors is not recommended. The application's behaviour cannot be predicted and it may fail in its attempt to generate outputs. Any outputs which have been created cannot be assumed to be valid. Use caution.**

```bash
$ infojson2csvqb build data.csv --config info.json --ignore-validation-errors
CSV: /Users/user/dataset/data.csv
info.json: /Users/user/dataset/info.json
Validation Error: Found neither QbObservationValue.unit nor QbMultiUnits defined. One of these must be defined.
Build Complete
```

Note that in this case any errors are still presented to you, but you also get the `Build Complete` message. This suggests that the build has been able to complete and you can find the outputs in the `./out` directory as usual.

## Validating Outputs

Even though the `infojson2csvqb` provides some new validation before generating your CSV-W, we are still relying on [csv-lint.rb](https://github.com/Data-Liberation-Front/csvlint.rb) to perform a number of validation checks on the resulting CSV-W. These checks include:

* enforcing foreign key relationships between the dataset and its local code-list,
* ensuring that all of a column's cells have the correct datatype,
* enforcing required cell values.

If you want to make sure that your datacube is as valid as possible, you should validate your CSV-W **before submitting** the job to Jenkins. Note that there are still some checks which Jenkins performs which cannot currently be run locally.

CSV-W validation can be run using the [csv-lint.rb](https://hub.docker.com/r/gsscogs/csvlint) docker image.

```bash
# Make sure you have the latest image accessible locally
docker pull gsscogs/csvlint
```

In order to validate your CSV-W, "simply" run the following command:

```bash
docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/csvlint csvlint -s <YOUR_MAIN_DATASET_CSVW_METADATA_FILE>
```

For example,

```bash
$ docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/csvlint csvlint -s ons-international-trade-in-services-by-subnational-areas-of-the-uk.csv-metadata.json 
..
/workspace/ons-international-trade-in-services-by-subnational-areas-of-the-uk.csv is VALID
..
/workspace/undefined-column.csv is VALID
```

This command will validate both your data cube CSV-W as well as any related local code-list CSV-Ws.

### SPARQL Tests

It is possible (if cumbersome) to go one step further than validation of your CSV-Ws. If you convert your CSV-Ws into RDF then it's possible to run the `SKOS` and `qb` SPARQL tests against the output.

Ensure you have the latest copies of the necessary docker images:

```bash
docker pull gsscogs/csv2rdf && docker pull gsscogs/gdp-sparql-tests
```

Convert your main dataset CSV-W into RDF/N-Triples:

```bash
docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/csv2rdf sh -c 'csv2rdf -u <YOUR_MAIN_DATASET_CSVW_METADATA_FILE> -m annotated | sed -e "s/file\:\//http\:\/\//g" | riot --syntax=Turtle --output=N-Triples' > my-rdf-output.nt
```

Convert each of the code-list CSV-Ws into RDF/N-Triples:

```bash
docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/csv2rdf sh -c 'csv2rdf -u <YOUR_CODE_LIST_CSVW_METADATA_FILE> -m annotated | sed -e "s/file\:\//http\:\/\//g" | riot --syntax=Turtle --output=N-Triples' > some-code-list-output.nt
```

**Concatenate together all the contents of each of you `.nt` files into one file `combined.nt`**. Now run first the `SKOS` SPARQL tests, followed by the `qb` SPARQL tests:

```bash
docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/gdp-sparql-tests sparql-test-runner -t /usr/local/tests/skos combined.nt
```

**If everything passes, you can expect to see no output from the command line. If you do see output, it's likely that something is wrong.**

Now we can run the `qb` SPARQL tests:

```bash
docker run -it --rm -v $(pwd):/workspace -w /workspace gsscogs/gdp-sparql-tests sparql-test-runner -t /usr/local/tests/qb combined.nt
```

N.B we can't run the `PMD` SPARQL tests yet because the CSV-W doesn't contain any of the PMD-specific triples needed for the platform.
