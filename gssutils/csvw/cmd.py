import argparse
import json
from pathlib import Path

from gssutils.csvw.namespaces import URI
from gssutils import CSVWMapping


def create_csvw():
    parser = argparse.ArgumentParser(description='Create CSVW JSON')
    parser.add_argument('mapping', type=argparse.FileType('r'),
                        help='Mapping from header columns to dimensions, measures and attributes')
    parser.add_argument('csv', type=argparse.FileType('r'),
                        help='Input CSV file.')
    args = parser.parse_args()
    csvw = CSVWMapping()
    csv_uri = URI(str(Path(args.csv.name)))
    csvw.set_input(csv_uri, args.csv)
    csvw.set_mapping(json.load(args.mapping))
    csvw.set_dataset_uri(csv_uri, csv_uri)
    csvw.write(URI(csv_uri + '-metadata.json'))
