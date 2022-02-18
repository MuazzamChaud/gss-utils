import json

from behave import when, then
import subprocess
from typing import Tuple
from csvcubeddevtools.behaviour.temporarydirectory import get_context_temp_dir_path


@when('the infojson2csvqb CLI is run with "{arguments}"')
def step_impl(context, arguments: str):
    command: str = f"infojson2csvqb {arguments.strip()}"
    (status_code, response) = run_command_in_temp_dir(context, command)
    context.infojson2csvqb_cli_result = (status_code, response)


@then("the infojson2csvqb CLI should succeed")
def step_impl(context):
    (status_code, response) = context.infojson2csvqb_cli_result
    assert status_code == 0, (status_code, response)
    assert "Build Complete" in response, response


@then("the infojson2csvqb CLI should fail with status code {status_code}")
def step_impl(context, status_code: str):
    (status_code, response) = context.infojson2csvqb_cli_result
    assert status_code == int(status_code), status_code


@then('the infojson2csvqb CLI should print "{printed_text}"')
def step_impl(context, printed_text: str):
    (status_code, response) = context.infojson2csvqb_cli_result
    assert printed_text in response, response

@then('the infojson2csvqb CLI should not print "{printed_text}"')
def step_impl(context, printed_text: str):
    (status_code, response) = context.infojson2csvqb_cli_result
    assert printed_text not in response, response


@then('the validation-errors.json file in the "{out_dir}" directory should contain')
def step_impl(context, out_dir: str):
    tmp_dir_path = get_context_temp_dir_path(context)
    expected_text_contents: str = context.text.strip()
    validation_errors_file = tmp_dir_path / out_dir / "validation-errors.json"
    assert validation_errors_file.exists()

    with open(validation_errors_file, "r") as f:
        file_contents = f.read()

    # Ensure JSON is valid.
    json_validation_errors = json.loads(file_contents)
    assert isinstance(json_validation_errors, list), type(json_validation_errors)

    assert expected_text_contents in file_contents, file_contents


def run_command_in_temp_dir(context, command: str) -> Tuple[int, str]:
    tmp_dir_path = get_context_temp_dir_path(context)
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=tmp_dir_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status_code = process.wait()
    response = process.stdout.read().decode("utf-8") + process.stderr.read().decode(
        "utf-8"
    )
    return status_code, response
