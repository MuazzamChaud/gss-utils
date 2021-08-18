from rdflib import URIRef, Literal
from rdflib.namespace import VOID

from gssutils.metadata import PMDCAT, DCAT, MARKDOWN, GDP
from gssutils.metadata import base, dcat
from gssutils.metadata.base import Status


class Catalog(dcat.Catalog):
    _type = PMDCAT.Catalog


class DatasetContents(base.Metadata):
    _type = PMDCAT.DatasetContents


class DataCube(DatasetContents):
    _type = PMDCAT.DataCube


class GraphDatasetContents(DatasetContents):
    _type = PMDCAT.GraphDatasetContents


class Ontology(DatasetContents):
    _type = PMDCAT.Ontology


class ConceptScheme(DatasetContents):
    _type = PMDCAT.ConceptScheme


class CatalogRecord(dcat.CatalogRecord):
    _type = DCAT.CatalogRecord
    _properties_metadata = dict(dcat.CatalogRecord._properties_metadata)
    _properties_metadata.update({
        'metadataGraph': (PMDCAT.metadataGraph, Status.mandatory, URIRef)
    })


class Dataset(dcat.Dataset):
    _type = PMDCAT.Dataset
    _properties_metadata = dict(dcat.Dataset._properties_metadata)
    _properties_metadata.update({
        'metadataGraph': (PMDCAT.metadataGraph, Status.mandatory, URIRef),
        # pmdcat:graph declares the graph containing the qb:DataSet
        'pmdcatGraph': (PMDCAT.graph, Status.mandatory, URIRef),
        'datasetContents': (PMDCAT.datasetContents, Status.mandatory, lambda d: URIRef(d.uri)),
        'markdownDescription': (PMDCAT.markdownDescription, Status.recommended, lambda l: Literal(l, datatype=MARKDOWN)),
        'sparqlEndpoint': (VOID.sparqlEndpoint, Status.mandatory, URIRef),
        'family': (GDP.family, Status.mandatory, GDP.term),
        'updateDueOn': (GDP.updateDueOn, Status.recommended, Literal)
    })

    def __init__(self, landingPage):
        super().__init__()
        self.landingPage = landingPage

    def __setattr__(self, key, value):
        if key == 'title':
            self.label = value
        elif key == 'publisher':
            self.creator = value
        elif key == 'description':
            # TODO: evaluate whether pmdcat:markdownDescription rdfs:subPropertyOf dct:description
            #       and if so, this is the wrong way around.
            #       See https://github.com/GSS-Cogs/gss-utils/issues/308
            self.markdownDescription = value
        super().__setattr__(key, value)
