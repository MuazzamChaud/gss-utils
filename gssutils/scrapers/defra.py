from dateutil.parser import parse
import logging
import mimetypes
from urllib.parse import urljoin

from lxml import html
from lxml.html import HtmlElement
from requests import Response

from .helpers import assert_get_one
from gssutils.metadata.dcat import Distribution
from gssutils.metadata.pmdcat import Dataset
from gssutils.metadata import GOV

def scrape(scraper, tree: HtmlElement):
    """
    We're treating the indicators landing page as a catalog. With each
    of the indicators linked from the page being a dataset.

    Here's an example of a catalog page: https://oifdata.defra.gov.uk/2/
    """

    scraper.catalog.title = assert_get_one(tree.xpath("//h1"),
        'Principle <h1> heading of catalog').text_content().strip()
    scraper.catalog.dataset = []
    scraper.catalog.publisher = GOV["department-for-environment-food-rural-affairs"]

    relative_contact_url = assert_get_one(tree.xpath('//a[contains(text(), "Contact us")]'),
        'Contact link <a> from footer').get("href")
    contact_url = urljoin(scraper.uri, relative_contact_url)
    r: Response = scraper.session.get(contact_url)
    if not r.ok:
        logging.warning('Unable to acquire contact point. You\'ll need to set this manually.')
        contact_point = ""
    else:
        contact_tree = html.fromstring(r.text)
        contact_point = assert_get_one(contact_tree.xpath("//address[@id='address-email']"),
            'Contract address.').text_content().strip()

    for dataset_element in tree.xpath("//body/div[@id='main-content']/div/div/div/span/a"):
        identifier = dataset_element.get("href")
        dataset_url = urljoin(scraper.uri, identifier)
        dataset = scrape_dataset(scraper, dataset_url, contact_point, identifier)
        if dataset:
            scraper.catalog.dataset.append(dataset)


def scrape_dataset(scraper, dataset_uri: str, contact_point: str, identifier: str) -> (Dataset):
    """
    Populate a single dataset using a single dataset page.
    Example page: https://oifdata.defra.gov.uk/2-1-1/
    """

    dataset = Dataset(scraper.uri)

    r: Response = scraper.session.get(dataset_uri)
    if not r.ok:
        logging.warning('Faliled to get datset {dataset_uri} with status code {r.status_code}')
        return None

    tree: HtmlElement = html.fromstring(r.text)

    title_element: HtmlElement = assert_get_one(tree.xpath('//h1'), 'title of dataset')
    dataset.title = title_element.text_content().strip()

    # To create the description, starting with the first <div> of the page content,
    # we want the text from all the the paragraph <p> elements
    # between the first and second headings <h2> elements.
    page_content_elements: HtmlElement = assert_get_one(tree.xpath("//div[@id='page-content']/div"), 
        'element containing bulk of page written content')

    heading_count = 0
    description_text = ""
    for element in page_content_elements:

        if element.tag.startswith("h"):
            heading_count +=1
        elif element.tag == "p":
            description_text += element.text_content() + "\n"
        
        if heading_count == 2:
            break

    dataset.description = description_text

    dataset.license = assert_get_one(tree.xpath("//div[@id='oglLicense']/a"), "licence in use").get("href")

    # we want the text from a table row <tr> that contains a table header <th> of text "Date last updated"
    issued_row_element = assert_get_one(tree.xpath("//tr/th[contains(text(),'Date last updated')]/parent::*"),
        'table row that contains header text of "Date last updated"')
    time_as_text = assert_get_one(issued_row_element.xpath('./td[1]'), 'Time from row text').text_content()
    dataset.issued = parse(time_as_text)

    dataset.contactPoint = "mailto:"+contact_point

    dataset.publisher = GOV["department-for-environment-food-rural-affairs"]

    # There's only one distribution of data and that's the source csv.
    distribution = Distribution(scraper)

    distribution.title = " ".join(dataset.title.split(" ")[1:])
    distribution.downloadURL = urljoin(scraper.uri, f'/en/data/{identifier}.csv')
    distribution.issued = dataset.issued

    distribution.mediaType, _ = mimetypes.guess_type(distribution.downloadURL)

    dataset.distribution = [distribution]

    return dataset

