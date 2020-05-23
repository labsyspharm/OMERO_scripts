#!/usr/bin/env python

from __future__ import print_function
from builtins import str
import sys
from argparse import ArgumentParser
from ..omero_basics import OMEROConnectionManager, write_csv
from omero.sys import ParametersI
from omero.rtypes import rtime
import datetime
import dateutil.parser

epoch = datetime.datetime.utcfromtimestamp(0)
periods = {
    'year': 'YYYY',
    'month': 'YYYY-MM',
    'day': 'YYYY-MM-DD'
}


def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0


def main(argv=sys.argv):

    # Configure argument parsing
    parser = ArgumentParser(description='''Report number of images imported in
                                           a date range''')
    parser.add_argument('-q', '--quiet', action='store_const', const=True,
                        default=False, help='Do not print output')
    parser.add_argument('-f', '--file', metavar='file',
                        help='Destination CSV file')
    parser.add_argument('-s', '--start', metavar='start',
                        help='Start timestamp')
    parser.add_argument('-e', '--end', metavar='end',
                        help='End timestamp')
    parser.add_argument('-a', '--all', action='store_const', const=True,
                        default=False,
                        help='Complete report. Ignores start/end')
    parser.add_argument('-p', '--period', choices=['year', 'month', 'day'],
                        default='month',
                        help='Period for use in conjunction with -a')
    args = parser.parse_args()

    # Create an OMERO Connection with our basic connection manager
    conn_manager = OMEROConnectionManager()

    if args.all:

        q = '''
            SELECT grp.name,
                   experimenter.omeName,
                   TO_CHAR(event.time, '{period}') AS cal_period,
                   count(event.time)
            FROM Image image
            JOIN image.details.creationEvent event
            JOIN image.details.owner experimenter
            JOIN image.details.group grp
            GROUP BY grp.name,
                     experimenter.omeName,
                     TO_CHAR(event.time, '{period}')
            ORDER BY grp.name,
                     experimenter.omeName,
                     TO_CHAR(event.time, '{period}')
            DESC
            '''

        q = q.format(period=periods[args.period])

        # Run the query
        rows = conn_manager.hql_query(q)
        header = ['Group', 'Username', 'Period', 'Count']

    else:

        params = ParametersI()
        params.map = {}

        start_date = None
        end_date = None

        try:
            if args.start:
                start_date = dateutil.parser.parse(args.start)
            if args.end:
                end_date = dateutil.parser.parse(args.end)
        except ValueError:
            sys.stderr.write('Start and/or end dates have to be parseable!')
            sys.exit(1)

        q = '''
            SELECT grp.name,
                   experimenter.omeName,
                   count(event.time)
            FROM Image image
            JOIN image.details.creationEvent event
            JOIN image.details.owner experimenter
            JOIN image.details.group grp
            '''

        if start_date or end_date:
            q += ' WHERE '

        if start_date:
            q += ' event.time >= :dstart '
            params.map['dstart'] = rtime(unix_time_millis(start_date))

        if start_date and end_date:
            q += ' AND '

        if end_date:
            q += ' event.time <= :dend'
            params.map['dend'] = rtime(unix_time_millis(end_date))

        q += '''
            GROUP BY grp.name,
                     experimenter.omeName
            '''

        # Run the query
        rows = conn_manager.hql_query(q, params)
        header = ['Group', 'Username', 'Count']

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
