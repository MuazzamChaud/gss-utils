import json
from gssutils.csvcubedintegration.configloaders.jsonschemavalidation import (
    validate_dict_against_schema_url,
)


def test_json_schema_validation_passes():
    value: dict = json.loads(
        """
        { 
            "id": "some-id",
            "published": "2020-01-01",
            "landingPage": "http://example.com/landing-page",
            "title" : "some title",
            "description" : "some description",
            "publisher" : "some publisher",
            "families" : ["some family"]
        }
        """
    )
    schema_url = "https://raw.githubusercontent.com/GSS-Cogs/family-schemas/main/dataset-schema-1.1.0.json"
    validation_errors = validate_dict_against_schema_url(value, schema_url)
    assert len(validation_errors) == 0, validation_errors


def test_json_schema_validation_fails():
    value: dict = json.loads(
        """
        { 
            "id": "some-id",
            "published": "2020-01-01",
            "landingPage": "http://example.com/landing-page",
            "title" : "some title",
            "description" : 3728,
            "publisher" : "some publisher",
            "families" : ["some family"]
        }
        """
    )
    schema_url = "https://raw.githubusercontent.com/GSS-Cogs/family-schemas/main/dataset-schema-1.1.0.json"

    validation_errors = validate_dict_against_schema_url(value, schema_url)
    assert len(validation_errors) == 1, validation_errors
    error = validation_errors[0]
    assert error.message == "3728 is not of type 'string'"
