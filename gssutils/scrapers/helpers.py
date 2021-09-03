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

def append_to_host_url(current_url: str, relative_url: str) -> (str):
    """Append a relative url to the host url"""
    scheme = urlparse(current_url).scheme
    host = urlparse(current_url).hostname
    return f'{scheme}://{host}{relative_url}'