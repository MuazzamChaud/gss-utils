from lxml.html import HtmlElement
from urllib.parse import urlparse

def assert_get_one(thing: HtmlElement, name_of_thing: str) -> (HtmlElement):
    """
    Helper to assert we have one of a thing when we're expecting one of a thing, then
    return that one thing de-listified
    """
    assert isinstance(thing, list), f'Aborting, helper function "assert_get_one" expected a list, got {type(thing)}' 
    assert len(thing) == 1, f'Aborting. Xpath expecting 1 "{name_of_thing}", got {len(thing)}'
    return thing[0]
