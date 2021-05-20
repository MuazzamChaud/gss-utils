"""
csv2rdf has been updated. It now means that URI templates are (correctly) being escaped.
e.g. `https://some.uri/{notation}` will transform a `notation` value of 'stu/ff' to 'stu%2Fff'.

Generally speaking, we don't want to URI encode values that we're placing in the `notation` column.
So we need to alter out URI templates to the `{+col_name}` for, e.g. `https://some.uri/{+notation}`
"""
from typing import Dict, Any
import re


keys_of_interest = ["propertyUrl", "valueUrl", "aboutUrl"]


def escape_uri_template_values(table_mapping: Dict):
    def _escape_uri_template_values(key: str, value: Any) -> Any:
        if isinstance(value, list):
            return [_escape_uri_template_values(key, v) for v in value]
        elif isinstance(value, dict):
            for k, v in value.items():
                value[k] = _escape_uri_template_values(k, v)
            return value
        elif key in keys_of_interest and isinstance(value, str):
            return re.sub(r"\{([^+]+)\}", r"{+\1}", value)
        else:
            return value

    _escape_uri_template_values("", table_mapping)

