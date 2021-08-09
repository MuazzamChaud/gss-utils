from behave import *

@step('set the temporalStart to "{date}"')
def step_impl(context, date):
    context.scraper.dataset.temporalStart = date

@step('set the temporalEnd to "{date}"')
def step_impl(context, date):
    context.scraper.dataset.temporalEnd = date

@step('set the temporalResolution to "{duration}"')
def step_impl(context, duration):
    context.scraper.dataset.temporalResolution = duration

@step('set spatial to "{uri}"')
def step_impl(context, uri):
    context.scraper.dataset.spatial = uri

@step('set the spatialResolution to "{uri}"')
def step_impl(context, uri):
    context.scraper.dataset.spatialResolution = uri