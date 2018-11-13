Feature: PMD metadata
  In an automated pipeline
  I want to build an RDF graph out of dataset metadata and ensure
  PMD specific terms are used.

  Scenario: generate metadata
    Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
    And set the base URI to <http://gss-data.org.uk>
    And set the dataset ID to <foreign-direct-investment-inward>
    And set the family to 'trade'
    And set the license to 'OGLv3'
    And set the modified time to '2018-09-14T10:04:33.141484+01:00'
    And set the description to 'Inward Foreign Direct Investment (FDI) Involving UK Companies, 2016 (Directional Principle)'
    And generate TriG
    Then the TriG should contain

      """
      @prefix dct: <http://purl.org/dc/terms/> .
      @prefix gdp: <http://gss-data.org.uk/def/gdp#> .
      @prefix ns1: <http://gss-data.org.uk/graph/foreign-direct-investment-inward/> .
      @prefix pmd: <http://publishmydata.com/def/dataset#> .
      @prefix qb: <http://purl.org/linked-data/cube#> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix void: <http://rdfs.org/ns/void#> .
      @prefix xml: <http://www.w3.org/XML/1998/namespace> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <http://gss-data.org.uk/graph/foreign-direct-investment-inward/metadata> {
        <http://gss-data.org.uk/data/foreign-direct-investment-inward> a pmd:Dataset,
          pmd:LinkedDataset,
          qb:DataSet ;
        rdfs:label "Foreign direct investment involving UK companies: Inward tables"@en ;
        gdp:family gdp:trade ;
        pmd:contactEmail <mailto:fdi@ons.gov.uk> ;
        pmd:graph <http://gss-data.org.uk/graph/foreign-direct-investment-inward> ;
        pmd:nextUpdateDue "2018-12-03"^^xsd:date ;
        dct:creator <https://www.gov.uk/government/organisations/office-for-national-statistics> ;
        dct:issued "2017-12-01"^^xsd:date ;
        dct:license <http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/> ;
        dct:modified "2018-09-14T10:04:33.141484+01:00"^^xsd:dateTime ;
        dct:publisher <https://www.gov.uk/government/organisations/office-for-national-statistics> ;
        dct:title "Foreign direct investment involving UK companies: Inward tables"@en ;
        void:sparqlEndpoint <http://gss-data.org.uk/sparql> ;
        rdfs:comment "Inward datasets including data for flows, positions and earnings."@en ;
        dct:description "Inward Foreign Direct Investment (FDI) Involving UK Companies, 2016 (Directional Principle)"^^<https://www.w3.org/ns/iana/media-types/text/markdown#Resource> .
      }
      """

    Scenario: convention over configuration
      Given the 'JOB_NAME' environment variable is 'GSS/Trade/ONS-FDI-inward'
      And I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
      And generate TriG
      Then the dataset URI should be <http://gss-data.org.uk/data/trade/ons-fdi-inward>
      And the metadata graph should be <http://gss-data.org.uk/graph/trade/ons-fdi-inward/metadata>
      And the modified date should be quite recent

    Scenario: licensed dataset
      Given I scrape the page "https://www.ons.gov.uk/businessindustryandtrade/business/businessinnovation/datasets/foreigndirectinvestmentinvolvingukcompanies2013inwardtables"
      Then dct:license should be `<http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>`