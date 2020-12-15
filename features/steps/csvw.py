import logging
from typing import Optional, List, TextIO

import gzip
import sys
import csv
import json
import time
from io import BytesIO, SEEK_END, StringIO, TextIOBase
from pathlib import Path
from tarfile import TarFile, TarInfo
from urllib.parse import urljoin

import docker as docker
import vcr
from behave import *
from nose.tools import *
from rdflib import Graph, Dataset

from gssutils import CSVWMetadata, CSVWMapping
from gssutils.csvw.namespaces import URI

DEFAULT_RECORD_MODE = 'new_episodes'


@given("table2qb configuration at '{url}'")
def step_impl(context, url):
    with vcr.use_cassette('features/fixtures/csvw.yml',
                          record_mode=context.config.userdata.get('record_mode',
                                                                  DEFAULT_RECORD_MODE)):
        context.schema = CSVWMetadata(url)


@step("a CSV file '{filename}'")
def step_impl(context, filename):
    context.csv_filename = Path(filename)
    if hasattr(context, 'table') and context.table is not None and hasattr(context.table, 'rows') and len(context.table.rows) > 0:
        context.csv_io = StringIO()
        writer = csv.writer(context.csv_io)
        writer.writerow(context.table.headings)
        for row in context.table:
            writer.writerow(row)
    else:
        csv_path = Path('features') / 'fixtures' / filename
        if filename.endswith("csv"):
            context.csv_io = open(csv_path, 'r', encoding='utf-8')
        elif filename.endswith("csv.gz"):
            context.csv_io = gzip.open(csv_path, mode='rt', encoding='utf-8')
        else:
            raise ValueError('Can only open files of type ".csv" and ".csv.gz" '
                            'not {}.'.format(filename))


@when("I create a CSVW schema '{filename}'")
def step_impl(context, filename):
    context.schema_filename = Path(filename)
    context.schema_io = StringIO()
    context.csv_io.seek(0)
    context.schema.create_io(
        context.csv_io,
        context.schema_io,
        str(context.csv_filename.relative_to(context.schema_filename.parent))
    )


@then("The schema is valid JSON")
def step_impl(context):
    context.schema_io.seek(0)
    json.load(context.schema_io)


@then("The input format of the csv is recorded as csv")
def step_impl(context):
    input_file = json.load(context.metadata_io)["tables"][0]["url"]
    assert input_file.endswith(".csv"), 'The input file should end .csv, got "{}"'.format(input_file)


@step("gsscogs/csvlint validates ok")
def step_impl(context):
    client = docker.from_env()
    csvlint = client.containers.create(
        'gsscogs/csvlint',
        command=f'csvlint -s /tmp/{context.schema_filename}'
    )
    archive = BytesIO()
    context.schema_io.seek(0, SEEK_END)
    schema_size = context.schema_io.tell()
    context.schema_io.seek(0)
    context.csv_io.seek(0, SEEK_END)
    csv_size = context.csv_io.tell()
    context.csv_io.seek(0)
    with TarFile(fileobj=archive, mode='w') as t:
        tis = TarInfo(str(context.schema_filename))
        tis.size = schema_size
        tis.mtime = time.time()
        t.addfile(tis, BytesIO(context.schema_io.getvalue().encode('utf-8')))
        tic = TarInfo(str(context.csv_filename))
        tic.size = csv_size
        tic.mtime = time.time()
        t.addfile(tic, BytesIO(context.csv_io.getvalue().encode('utf-8')))
    archive.seek(0)
    csvlint.put_archive('/tmp/', archive)
    csvlint.start()
    response = csvlint.wait()
    sys.stdout.write(csvlint.logs().decode('utf-8'))
    assert_equal(response['StatusCode'], 0)


@when("I create a CSVW metadata file '{filename}' for base '{base}' and path '{path}'")
def step_impl(context, filename, base, path):
    context.metadata_filename = Path(filename)
    context.metadata_io = StringIO()
    context.csv_io.seek(0)
    if hasattr(context, 'json_io'):
        context.json_io.seek(0)
        context.schema.create_io(
            context.csv_io,
            context.metadata_io,
            str(context.csv_filename.relative_to(context.metadata_filename.parent)),
            mapping=context.json_io,
            base_url=base,
            base_path=path,
            with_external=False
        )
    else:
        context.schema.create_io(
            context.csv_io,
            context.metadata_io,
            str(context.csv_filename.relative_to(context.metadata_filename.parent)),
            with_transform=True,
            base_url=base,
            base_path=path,
            with_external=False
        )


@then("the metadata is valid JSON-LD")
def step_impl(context):
    g = Graph()
    context.metadata_io.seek(0)
    g.parse(source=BytesIO(context.metadata_io.getvalue().encode('utf-8')), format='json-ld')


def run_csv2rdf(csv_filename: str, metadata_filename: str, csv_io: TextIO, metadata_io: TextIO):
    client = docker.from_env()
    csv2rdf = client.containers.create(
        'gsscogs/csv2rdf',
        command=f'csv2rdf -m annotated -o /tmp/output.ttl -t /tmp/{csv_filename} -u /tmp/{metadata_filename}'
    )
    archive = BytesIO()
    metadata_io.seek(0, SEEK_END)
    metadata_size = metadata_io.tell()
    metadata_io.seek(0)
    csv_io.seek(0, SEEK_END)
    csv_size = csv_io.tell()
    csv_io.seek(0)
    with TarFile(fileobj=archive, mode='w') as t:
        tis = TarInfo(str(metadata_filename))
        tis.size = metadata_size
        tis.mtime = time.time()
        t.addfile(tis, BytesIO(metadata_io.read().encode('utf-8')))
        tic = TarInfo(str(csv_filename))
        tic.size = csv_size
        tic.mtime = time.time()
        t.addfile(tic, BytesIO(csv_io.read().encode('utf-8')))
    archive.seek(0)
    csv2rdf.put_archive('/tmp/', archive)
    csv2rdf.start()
    response = csv2rdf.wait()
    sys.stdout.write(csv2rdf.logs().decode('utf-8'))
    assert_equal(response['StatusCode'], 0)
    output_stream, output_stat = csv2rdf.get_archive('/tmp/output.ttl')
    output_archive = BytesIO()
    for line in output_stream:
        output_archive.write(line)
    output_archive.seek(0)
    with TarFile(fileobj=output_archive, mode='r') as t:
        output_ttl = t.extractfile('output.ttl')
        return output_ttl.read()


@step("gsscogs/csv2rdf generates RDF")
def step_impl(context):
    context.turtle = run_csv2rdf(context.csv_filename, context.metadata_filename, context.csv_io, context.metadata_io)


@when("I create a CSVW metadata file '{filename}' for base '{base}' and path '{path}' with dataset metadata")
def step_impl(context, filename, base, path):
    context.metadata_filename = Path(filename)
    context.metadata_io = StringIO()
    context.csv_io.seek(0)
    context.scraper.set_base_uri(urljoin(base, '/'))
    context.scraper.set_dataset_id(path)
    quads = context.scraper.as_quads()
    context.schema.create_io(
        context.csv_io,
        context.metadata_io,
        str(context.csv_filename.relative_to(context.metadata_filename.parent)),
        with_transform=True,
        base_url=base,
        base_path=path,
        dataset_metadata=quads
    )


def run_ics(group: str, turtle: bytes, extra_files: List[str] = (), extra_data: List[str] = ()):
    client = docker.from_env()
    files = ['data.ttl']
    if len(extra_files) > 0:
        files.extend(extra_files)
    tests = client.containers.create(
        'gsscogs/gdp-sparql-tests',
        command=f'''sparql-test-runner -t /usr/local/tests/{group} -p dsgraph='<urn:x-arq:DefaultGraph>' '''
                f'''{" ".join('/tmp/' + f for f in files)}'''
    )
    archive = BytesIO()
    with TarFile(fileobj=archive, mode='w') as t:
        ttl = TarInfo('data.ttl')
        ttl.size = len(turtle)
        ttl.mtime = time.time()
        t.addfile(ttl, BytesIO(turtle))
        for filename in extra_files:
            actual_path = Path('features') / 'fixtures' / 'extra' / filename
            with actual_path.open('rb') as actual_file:
                extra_file = t.gettarinfo(arcname=filename, fileobj=actual_file)
                t.addfile(extra_file, actual_file)
        for i, add_turtle in enumerate(extra_data):
            filename = f'extra_{i}.ttl'
            add_ttl = TarInfo(filename)
            add_ttl.size = len(add_turtle)
            add_ttl.mtime = time.time()
            t.addfile(add_ttl, BytesIO(add_turtle.encode('utf-8')))
            files.append(filename)
    archive.seek(0)
    tests.put_archive('/tmp/', archive)
    tests.start()
    response = tests.wait()
    sys.stdout.write(tests.logs().decode('utf-8'))
    return response['StatusCode']


@step("the RDF should pass the Data Cube integrity constraints")
def step_impl(context):
    result = run_ics('qb', context.turtle)
    if result != 0:
        logging.warning("Some ICs failed.")


@step("a JSON map file '{map_file}'")
def step_impl(context, map_file):
    context.json_filename = Path(map_file)
    context.json_io = StringIO()
    mapping = json.load(open(Path('features') / 'fixtures' / map_file))
    json.dump(mapping, context.json_io)


@step("component registry at '{url}'")
def step_impl(context, url):
    context.schema = CSVWMetadata(url)


@when("I create a CSVW file from the mapping and CSV")
def step_impl(context):
    context.csvw = CSVWMapping()
    context.csv_io.seek(0)
    context.csvw.set_input(context.csv_filename, context.csv_io)
    context.json_io.seek(0)
    context.csvw.set_mapping(json.load(context.json_io))
    if hasattr(context, 'registry'):
        context.csvw.set_registry(URI(context.registry))
    if hasattr(context, 'dataset_uri'):
        context.csvw.set_dataset_uri(context.dataset_uri)
    context.metadata_io = StringIO()
    context.metadata_filename = context.csv_filename.with_name(context.csv_filename.name + '-metadata.json')
    context.csvw.write(context.metadata_io)


@step("a registry at '{endpoint}'")
def step_impl(context, endpoint):
    context.registry = endpoint


@step("a dataset URI '{uri}'")
def step_impl(context, uri):
    context.dataset_uri = uri


@step("the RDF should pass the PMD4 constraints")
def step_impl(context):
    if hasattr(context, 'extra_files') and len(context.extra_files) > 0:
        result = run_ics('pmd/pmd4', context.turtle, context.extra_files)
    else:
        result = run_ics('pmd/pmd4', context.turtle)
    assert_equal(result, 0)


@step('I add extra RDF files "{files}"')
def step_impl(context, files):
    context.extra_files = [f.strip() for f in files.split(',')]


@step('I add local codelists "{files}"')
def step_impl(context, files):
    codelists = [f.strip() for f in files.split(',')]
    context.extra_data = []
    for csv in codelists:
        csv_path = Path('features') / 'fixtures' / 'extra' / csv
        metadata_path = csv_path.with_suffix('.csv-metadata.json')
        with csv_path.open('r') as csv_file, metadata_path.open('r') as metadata_file:
            context.extra_data.append(run_csv2rdf(csv_path.name, metadata_file.name, csv_file, metadata_file))


@step("a column map")
def step_impl(context):
    mapping = {'transform': {'columns': json.loads(context.text)}}
    context.json_io = StringIO()
    json.dump(mapping, context.json_io)