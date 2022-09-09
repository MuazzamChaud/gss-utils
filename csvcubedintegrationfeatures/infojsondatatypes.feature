Feature: Test that any specified datatypes are correctly persisted

  Scenario: The infojson2csvqb build command should output cubes with the correct datatypes
    Given the existing test-case file "configloaders/infojson1-1/datatypes.csv"
    And the existing test-case file "configloaders/infojson1-1/datatypes.json"
    When the infojson2csvqb CLI is run with "build --config configloaders/infojson1-1/datatypes.json configloaders/infojson1-1/datatypes.csv"
    Then the infojson2csvqb CLI should succeed
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    # Confirm that the types have been assigned as expected
    And the RDF should contain
    """

    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/anyuri-attribute> rdfs:label "anyURI attribute"@en;
      rdfs:range xsd:anyURI .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/boolean-attribute> rdfs:label "boolean attribute"@en;
      rdfs:range xsd:boolean .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/decimal-attribute> rdfs:label "decimal attribute"@en;
      rdfs:range xsd:decimal .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/int-attribute> rdfs:label "int attribute"@en;
      rdfs:range xsd:int .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/long-attribute> rdfs:label "long attribute"@en;
      rdfs:range xsd:long .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/integer-attribute> rdfs:label "integer attribute"@en;
      rdfs:range xsd:integer .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/short-attribute> rdfs:label "short attribute"@en;
      rdfs:range xsd:short .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/nonnegativeinteger-attribute> rdfs:label "nonNegativeInteger attribute"@en;
      rdfs:range xsd:nonNegativeInteger .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/positiveinteger-attribute> rdfs:label "positiveInteger attribute"@en;
      rdfs:range xsd:positiveInteger .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedlong-attribute> rdfs:label "unsignedLong attribute"@en;
      rdfs:range xsd:unsignedLong .
 
    <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedint-attribute> rdfs:label "unsignedInt attribute"@en;
      rdfs:range xsd:unsignedInt .
 
    <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedshort-attribute> rdfs:label "unsignedShort attribute"@en;
      rdfs:range xsd:unsignedShort .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/nonpositiveinteger-attribute> rdfs:label "nonPositiveInteger attribute"@en;
      rdfs:range xsd:nonPositiveInteger .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/negativeinteger-attribute> rdfs:label "negativeInteger attribute"@en;
      rdfs:range xsd:negativeInteger .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/double-attribute> rdfs:label "double attribute"@en;
      rdfs:range xsd:double .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/float-attribute> rdfs:label "float attribute"@en;
      rdfs:range xsd:float .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/string-attribute> rdfs:label "string attribute"@en;
      rdfs:range xsd:string .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/language-attribute> rdfs:label "language attribute"@en;
      rdfs:range xsd:language .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/date-attribute> rdfs:label "date attribute"@en;
      rdfs:range xsd:date .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/datetime-attribute> rdfs:label "dateTime attribute"@en;
      rdfs:range xsd:dateTime .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/datetimestamp-attribute> rdfs:label "dateTimeStamp attribute"@en;
      rdfs:range xsd:dateTimeStamp .

    <file:/tmp/datatypes-fixture-dataset.csv#attribute/time-attribute> rdfs:label "time attribute"@en;
      rdfs:range xsd:time .
    """
    # confirm that the output values are formatted as expected
    And the RDF should contain
    """
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    <file:/tmp/datatypes-fixture-dataset.csv#obs/00,01,02@count> <file:/tmp/datatypes-fixture-dataset.csv#attribute/anyuri-attribute> "http://www.foo.com"^^xsd:anyURI ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/boolean-attribute> true ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/date-attribute> "2019-09-07"^^xsd:date ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/datetime-attribute> "2019-09-07T15:50:00"^^xsd:dateTime ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/datetimestamp-attribute> "2004-04-12T13:20:00Z"^^xsd:dateTimeStamp ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/decimal-attribute> 0.11 ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/double-attribute> 3.142e-02 ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/float-attribute> "0.03142"^^xsd:float ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/int-attribute> "-1"^^xsd:int ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/integer-attribute> -1 ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/language-attribute> "english"^^xsd:language ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/long-attribute> "-2147483647"^^xsd:long ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/negativeinteger-attribute> "-1"^^xsd:negativeInteger ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/nonnegativeinteger-attribute> "1"^^xsd:nonNegativeInteger ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/nonpositiveinteger-attribute> "-1"^^xsd:nonPositiveInteger ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/positiveinteger-attribute> "1"^^xsd:positiveInteger ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/short-attribute> "-32768"^^xsd:short ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/string-attribute> "foo" ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/time-attribute> "14:30:43"^^xsd:time ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedint-attribute> "1"^^xsd:unsignedInt ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedlong-attribute> "2147483646"^^xsd:unsignedLong ;
      <file:/tmp/datatypes-fixture-dataset.csv#attribute/unsignedshort-attribute> "32768"^^xsd:unsignedShort .
    """