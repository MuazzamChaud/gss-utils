import numpy as np
import vcr
from behave import *

from gssutils import *

DEFAULT_RECORD_MODE = 'new_episodes'


def get_fixture(file_name: str) -> Path:
    """Helper to get specific files out of the fixtures dir"""
    feature_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    fixture_file_path = Path(feature_path, "fixtures", file_name)
    return fixture_file_path


@given('I scrape datasets using info.json "{fixture_path}"')
def step_impl(context, fixture_path):
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                          record_mode=context.config.userdata.get('record_mode', 'DEFAULT_RECORD_MODE')):
        context.scraper = Scraper(seed=str(get_fixture(fixture_path)))


@given('I select the latest distribution as the distro')
def step_impl(context):
    context.distro = context.scraper.distribution(latest=True)


@given(u'PMD chunks of')
def step_impl(context):
    context.pmd_chunks = [x.strip() for x in context.text.split(",")]


@given(u'odata API chunks of')
def step_impl(context):
    context.odata_chunks = [x.strip() for x in context.text.split(",")]


@given(u'I specify the required chunk as')
def step_impl(context):
    context.required_chunks = [x.strip() for x in context.text.split(",")]


@given('fetch the initial data from the API endpoint')
def step_impl(context):
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                          record_mode=context.config.userdata.get('record_mode', 'DEFAULT_RECORD_MODE')):
        context.df = context.distro._get_principle_dataframe(chunks_wanted=context.required_chunks)


@given('fetch the supplementary data from the API endpoint')
def step_impl(context):
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                          record_mode=context.config.userdata.get('record_mode', 'DEFAULT_RECORD_MODE')):
        context.supplementary_datasets = context.distro._get_supplementary_dataframes()


@given(u'I specify the chunk column as "{chunk_column_name}"')
def step_impl(context, chunk_column_name):
    context.chunk_column_name = chunk_column_name


@then('the row count is "{row_count}"')
def step_impl(context, row_count):
    assert context.df.shape[0] == int(row_count), \
        f"Record count does not match expected value. Expected:\n {row_count}\v\nGot:\n{context.df.shape[0]}"


@then('the column count is "{column_count}"')
def step_impl(context, column_count):
    assert context.df.shape[1] == int(column_count), \
        f"Record count does not match expected value. Expected:\n {column_count}\v\nGot:\n{context.df.shape[1]}"


@then('the chunk column only contains the required chunks')
def step_impl(context):
    assert context.df[context.chunk_column_name].isin(context.required_chunks).all(), \
        f"Chunk column contains unexpected data. Expected a null set."


@then('I identify the chunks for that dataset on the API as')
def step_impl(context):
    with vcr.use_cassette("features/fixtures/cassettes/odata_api.yml",
                          record_mode=context.config.userdata.get('record_mode', 'DEFAULT_RECORD_MODE')):
        api_chunks = list(set(context.distro.get_odata_api_chunks()))
        expected_chunks = [int(x.strip()) for x in context.text.split(",")]
        assert set(api_chunks) == set(expected_chunks), \
            f'Expecting "{expected_chunks}". \nGot "{api_chunks}".'


@then('I identify the chunks for that dataset on PMD as')
def step_impl(context):
    with vcr.use_cassette("features/fixtures/cassettes/pmd4.yml",
                          record_mode=context.config.userdata.get('record_mode', 'DEFAULT_RECORD_MODE')):
        pmd_chunks = list(set(context.distro.get_pmd_chunks()))
        expected_chunks = [x.strip() for x in context.text.split(",")]
        assert set(pmd_chunks) == set(expected_chunks), \
            f'Expecting "{expected_chunks}". \nGot "{pmd_chunks}".'


@then('the names and sizes equate to')
def step_impl(context):
    for row in context.table:
        key = row[0]
        assert key in context.supplementary_datasets, \
            f'Dataframe "{key}" not in dictionary but was expected.'

        expected_shape = tuple(int(x) for x in row[1].split(','))
        got_shape = context.supplementary_datasets[key].shape

        assert got_shape == expected_shape, \
            f'Dataframe "{key}".shape() does not match expected. Got \n"{got_shape}"\n, but expected \n"{expected_shape}"\n.'


@then(u'I merge the dataframes based on primary keys')
def step_impl(context):
    context.df_merged = context.distro._merge_principle_supplementary_dataframes(
        context.df, context.supplementary_datasets)


@then('the merged row count is "{row_count}"')
def step_impl(context, row_count):
    assert context.df_merged.shape[0] == int(row_count), \
        f"Record count does not match expected value. Expected:\n {row_count}\v\nGot:\n{context.df.shape[0]}"


@then('the merged column count is "{column_count}"')
def step_impl(context, column_count):
    assert context.df_merged.shape[1] == int(column_count), \
        f"Record count does not match expected value. Expected:\n {column_count}\v\nGot:\n{context.df.shape[1]}"


@then(u'the sum of the value columns equate to')
def step_impl(context):
    for row in context.table:
        column = row[0]
        total = np.float(row[1])

        assert context.df_merged[column].sum() == total, \
            f'Dataframe column "{column}" had value {context.df_merged[column].sum()}, expected {total}.'
