from io import StringIO
from urllib.parse import urlparse

import rdflib
from dateutil.parser import parse
from rdflib import RDF, URIRef
from rdflib.namespace import DCTERMS
from pyRdfa import pyRdfa as rdfa_processor, Options, HostLanguage

from gssutils.metadata import DCAT, GOV
from gssutils.metadata.dcat import Distribution


def scrape(scraper, tree):
    page = StringIO(scraper.session.get(scraper.uri).text)
    pageGraph = _parse_rdfa_to_graph(page)
    # pageGraph.parse(page, format="html")
    dataset = pageGraph.value(predicate=RDF.type, object=DCAT.Dataset, any=False)
    scraper.dataset.title = pageGraph.value(dataset, DCTERMS.title).value.strip()
    scraper.dataset.comment = pageGraph.value(
        dataset, DCTERMS.description
    ).value.strip()
    license = str(pageGraph.value(dataset, DCTERMS.license))
    if license == "http://www.nationalarchives.gov.uk/doc/open-government-licence":
        scraper.dataset.license = (
            "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        )
    else:
        scraper.dataset.license = license
    publisher = pageGraph.value(dataset, DCTERMS.publisher)
    if publisher == URIRef("http://www.gov.wales/"):
        scraper.dataset.publisher = GOV["welsh-government"]
    else:
        scraper.dataset.publisher = publisher
    scraper.dataset.issued = parse(
        pageGraph.value(dataset, DCTERMS.created), dayfirst=True
    ).date()
    scraper.dataset.modified = parse(
        pageGraph.value(dataset, DCTERMS.modified), dayfirst=True
    ).date()
    for pageDist in pageGraph.subjects(RDF.type, DCAT.Distribution):
        dist = Distribution(scraper)
        dist.title = pageGraph.value(pageDist, DCTERMS.title).value.strip()
        # Access URLs seem to have spaces in their query strings
        url_parts = urlparse(pageGraph.value(pageDist, DCAT.accessURL))
        dist.downloadURL = url_parts._replace(
            query=url_parts.query.replace(" ", "+")
        ).geturl()
        dist.mediaType = pageGraph.value(pageDist, DCAT.mediaType).value.strip()
        scraper.distributions.append(dist)


def _parse_rdfa_to_graph(page: StringIO) -> rdflib.Graph:
    options = Options()
    options.host_language = HostLanguage.html5
    processor = rdfa_processor(options)
    return processor.graph_from_source(page)
