from behave import *
from pathlib import Path
from nose.tools import *
import hashlib

from gssutils import Scraper


@step("the fixtures directory is empty")
def step_impl(context):
    fixtures = Path('fixtures')
    if fixtures.exists() and fixtures.is_dir():
        for f in fixtures.iterdir():
            assert f.is_file()
            f.unlink()
        fixtures.rmdir()
    assert not fixtures.exists()


@step('I directly scrape the page "{uri}"')
def step_impl(context, uri):
    context.scraper = Scraper(uri)
    print(context.scraper._repr_markdown_())


def file_hash(filename):
    with open(filename, 'rb') as f:
        hash = hashlib.sha256()
        while chunk := f.read(4096):
            hash.update(chunk)
        return hash.hexdigest()


@step('the fixtures directory has a file "{filename}"')
def step_impl(context, filename):
    fixtures = Path('fixtures')
    assert fixtures.exists()
    assert fixtures.is_dir()
    assert (fixtures / filename).exists()
    # remember the file state
    if not hasattr(context, 'filestats'):
        context.filestats = {}
    context.filestats[filename] = (fixtures / filename).stat()
    if not hasattr(context, 'filehash'):
        context.filehash = {}
    context.filehash[filename] = file_hash(fixtures / filename)


@then('the fixtures file "{filename}" should not change')
def step_impl(context, filename):
    fixture_file = Path('fixtures') / filename
    eq_(context.filestats[filename], fixture_file.stat())
    eq_(context.filehash[filename], file_hash(fixture_file))


@step("directly fetch the distribution as a databaker object")
def step_impl(context):
    if not hasattr(context, 'distribution'):
        context.distribution = context.scraper.distribution(latest=True)
    context.databaker = context.distribution.as_databaker(latest=True)
