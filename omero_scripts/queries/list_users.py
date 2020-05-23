#!/usr/bin/env python

from __future__ import print_function
from builtins import str
import sys
from argparse import ArgumentParser
from ..omero_basics import OMEROConnectionManager, write_csv
from omero.sys import ParametersI


def main(argv=sys.argv):

    # Configure argument parsing
    parser = ArgumentParser(description='''List user details''')
    parser.add_argument('-q', '--quiet', action='store_const', const=True,
                        default=False, help='Do not print output')
    parser.add_argument('-f', '--file', metavar='file',
                        help='Destination CSV file')
    args = parser.parse_args()

    # Create an OMERO Connection with our basic connection manager
    conn_manager = OMEROConnectionManager()

    q = '''
        SELECT experimenter.omeName,
               experimenter.firstName,
               experimenter.lastName,
               experimenter.institution,
               experimenter.email,
               experimenter.id
        FROM Experimenter experimenter
        ORDER BY experimenter.omeName
        DESC
        '''

    # Run the query
    rows = conn_manager.hql_query(q)
    header = ['Username', 'Firstname', 'Lastname', 'Institution', 'Email',
              'ID']

    # Print results (if not quieted)
    if args.quiet is False:
        print(', '.join(header))
        for row in rows:
            print(', '.join([str(item) for item in row]))

    # Output CSV file (if specified)
    if args.file is not None:
        write_csv(rows,
                  args.file,
                  header)


if __name__ == '__main__':
    main()
