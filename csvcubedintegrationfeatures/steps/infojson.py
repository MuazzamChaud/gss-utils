from csvcubed.models.cube import QbCube
from csvcubed.utils.qb.validation.cube import validate_qb_component_constraints
from csvcubeddevtools.behaviour.temporarydirectory import get_context_temp_dir_path
from behave import Step, When, Then
from csvcubed.writers.qbwriter import QbWriter
from csvcubed.models.cube.uristyle import URIStyle

import gssutils.csvcubedintegration.configloaders.infojson as infojsonloader


@Step(
    'we load a cube using the info.json from "{some_json}" with CSV from "{some_csv}"'
)
def step_impl(context, some_json, some_csv):
    tmp_dir = get_context_temp_dir_path(context)

    cube_value, validation_errors, json_schema_validation_errors = infojsonloader.get_cube_from_info_json(
        tmp_dir / some_json,
        tmp_dir / some_csv,
    )

    context.cube = cube_value
    context.validation_errors = validation_errors
    context.json_schema_validation_errors = json_schema_validation_errors


@Step("the CSVqb should pass all validations")
def step_impl(context):
    cube: QbCube = context.cube
    errors = cube.validate()
    context.validation_errors += validate_qb_component_constraints(context.cube)
    assert len(context.validation_errors) == 0, [e.message for e in context.validation_errors]


@When("the cube is serialised to CSV-W")
def step_impl(context):
    writer = QbWriter(context.cube)
    temp_dir = get_context_temp_dir_path(context)
    writer.write(temp_dir)


@Then("there are no JSON schema validation errors")
def step_impl(context):
    assert len(context.json_schema_validation_errors) == 0, [
        e.message for e in context.json_schema_validation_errors
    ]


@Then("some additional turtle is appended to the resulting RDF")
def step_impl(context):
    rdf_to_add = context.text
    context.turtle += rdf_to_add


@Then("there is the following JSON schema validation error")
def step_impl(context):
    actual_errors: list[str] = [e.message for e in context.json_schema_validation_errors]
    expected_error: str = context.text.strip()
    assert expected_error in actual_errors


@Then("the cube should be configured with WithoutFileExtensions uri style")
def step_impl(context):
    assert context.cube.uri_style == URIStyle.WithoutFileExtensions, f"Expected URIStyle.WithoutFileExtensions but found {context.cube.uri_style}"
