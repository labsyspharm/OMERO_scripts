#!/usr/bin/env python

from argparse import ArgumentParser
from omero_basics import OMEROConnectionManager
from omero_basics import write_csv

# Configure argument parsing
parser = ArgumentParser(description='List all projects and child datasets'
                        'visible to the user')
group = parser.add_mutually_exclusive_group()
group.add_argument('-q', '--quiet', action='store_true',
                   help="Do not print output")
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
    header.append('Project Name')

q += """
           project.id,
           project.details.owner.omeName,
     """
header.extend(['Project ID', 'Project Owner'])

if not args.nonames:
    q += ' dataset.name, '
    header.append('Dataset Name')

q += """
           dataset.id,
           dsowner.omeName
    from Project project
    left outer join project.datasetLinks pdlink
    left outer join pdlink.child dataset
    left outer join dataset.details.owner dsowner
    """

# Run the query
rows = conn_manager.hql_query(q)

header.extend(['Dataset ID', 'Dataset Owner'])

# Print results (if not quieted)
if args.quiet is False:
    print ', '.join(header)
    for row in rows:
        print ', '.join([str(item) for item in row])

# Output CSV file (if specified)
if args.file is not None:
    write_csv(rows, args.file, header)
