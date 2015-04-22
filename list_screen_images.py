#!/usr/bin/env python

from argparse import ArgumentParser
from omero_basics import OMEROConnectionManager
from omero_basics import write_csv
from omero_basics import well_from_row_col

# Configure argument parsing
parser = ArgumentParser(description='List all images in a screen')
parser.add_argument('screen', type=int)
parser.add_argument('-q', '--quiet', action='store_const', const=True,
                    default=False, help="Do not print output")
parser.add_argument('-f', '--file', metavar='file',
                    help='Destination CSV file')
args = parser.parse_args()

# Create an OMERO Connection with our basic connection manager
conn_manager = OMEROConnectionManager()

# Define a query to get the list of images in a screen complete with
# well ID, plate ID, Plate Description and Screen Name. Only queries the
# first field
q = """
    select slink.parent.name,
           plate.name,
           plate.id,
           well.row,
           well.column,
           ws.image.id
    from Well well,
         Plate plate
    join well.wellSamples ws
    join plate.screenLinks slink
    where index(ws)=0
    and slink.parent.id=%i
    """ % args.screen

# Run the query
rows = conn_manager.hql_query(q)

# Replace Row+Column IDs with a more meaningful Well designation
# E.g. Row 3, Column 2: D3
for row in rows:

    # Calculate the Well and assign it to the position that row was in
    row[3] = well_from_row_col(row[3], row[4])

    # Remove the column field altogether
    row.pop(4)

# Print results (if not quieted)
if args.quiet is False:
    for row in rows:
        print row

# Output CSV file (if specified)
if args.file is not None:
    write_csv(rows, args.file, ["Screen Name", "Plate Name",
                                 "Plate ID", "Well", "Image ID"])

