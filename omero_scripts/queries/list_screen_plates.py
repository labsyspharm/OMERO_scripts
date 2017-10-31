#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from ..omero_basics import OMEROConnectionManager, write_csv


def main(argv=sys.argv):

    # Configure argument parsing
    parser = ArgumentParser(description='List all plates in a screen')
    parser.add_argument('screen', type=int)
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
        q += ' screen.name, '
        q += ' plate.name, '
        header.append('Screen Name')
        header.append('Plate Name')

    q += """
               plate.id
        from Plate plate
        join plate.screenLinks slink
        join slink.parent screen
        where slink.parent.id=%i
        """ % args.screen

    # Run the query
    rows = conn_manager.hql_query(q)

    header.append('Plate ID')

    # Print results (if not quieted)
    if args.quiet is False:
        print ', '.join(header)
        for row in rows:
            print ', '.join([str(item) for item in row])

    # Output CSV file (if specified)
    if args.file is not None:
        write_csv(rows, args.file, header)


if __name__ == '__main__':
    main()
