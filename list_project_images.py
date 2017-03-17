#!/usr/bin/env python

from argparse import ArgumentParser
from omero_basics import OMEROConnectionManager
from omero_basics import write_csv

# Configure argument parsing
parser = ArgumentParser(description='List all images in a project')
parser.add_argument('project', type=int)
parser.add_argument('-q', '--quiet', action='store_const', const=True,
                    default=False, help='Do not print output')
parser.add_argument('-n', '--nonames', action='store_const', const=True,
                    default=False, help='Do not print names')
parser.add_argument('-f', '--file', metavar='file',
                    help='Destination CSV file')
args = parser.parse_args()

# Create an OMERO Connection with our basic connection manager
conn_manager = OMEROConnectionManager()

q = 'select'
header = []

if not args.nonames:
    q += ' project.name, '
    q += ' dataset.name, '
    header.append('Project Name')
    header.append('Dataset Name')

q += ' dataset.id, '
header.append('Dataset ID')

if not args.nonames:
    q += ' image.name, '
    header.append('Image Name')

q += """
           image.id
    from Project project
    join project.datasetLinks dlink
    join dlink.child dataset
    join dataset.imageLinks iLink
    join iLink.child image
    where project.id=%i
    """ % args.project

# Run the query
rows = conn_manager.hql_query(q)

header.append('Image ID')

# Print results (if not quieted)
if args.quiet is False:
    print ', '.join(header)
    for row in rows:
        print ', '.join([str(item) for item in row])

# Output CSV file (if specified)
if args.file is not None:
    write_csv(rows, args.file, header)
