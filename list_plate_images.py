#!/usr/bin/env python

from argparse import ArgumentParser
from omero_basics import OMEROConnectionManager
from omero_basics import write_csv
from omero_basics import well_from_row_col

# Configure argument parsing
parser = ArgumentParser(description='List all images in a plate')
parser.add_argument('plate', type=int)
parser.add_argument('-q', '--quiet', action='store_const', const=True,
                    default=False, help="Do not print output")
parser.add_argument('-n', '--nonames', action='store_const', const=True,
                    default=False, help='Do not print names')
parser.add_argument('-f', '--file', metavar='file',
                    help='Destination CSV file')
args = parser.parse_args()

# Create an OMERO Connection with our basic connection manager
conn_manager = OMEROConnectionManager()

# Define a query to get the list of image ID in a screen complete with
# screen name, plate ID and well row/column. Only queries the first field.
q = 'select'
header = []
first_well = 2

if not args.nonames:
    q += ' plate.name, '
    header.append('Plate Name')
    first_well += 1

q += """
           plate.id,
           index(ws),
           well.row,
           well.column,
           ws.image.id
    from Well well
    join well.plate plate
    join well.wellSamples ws
    where plate.id=%i
    order by plate.id,
             index(ws),
             well.row,
             well.column,
             ws.image.id
    """ % args.plate

# Run the query
rows = conn_manager.hql_query(q)

# Replace Row+Column IDs with a more meaningful Well designation
# E.g. Row 3, Column 2: D3
for row in rows:

    # Calculate the Well and assign it to the position that row was in
    row[first_well] = well_from_row_col(row[first_well], row[first_well+1])

    # Remove the column field altogether
    row.pop(first_well+1)


header.extend(['Plate ID', 'Field', 'Well', 'Image ID'])

# Print results (if not quieted)
if args.quiet is False:
    print ', '.join(header)
    for row in rows:
        print ', '.join([str(item) for item in row])

# Output CSV file (if specified)
if args.file is not None:
    write_csv(rows, args.file, header)
