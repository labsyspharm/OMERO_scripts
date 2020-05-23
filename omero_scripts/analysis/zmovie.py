#!/usr/bin/env python

from __future__ import division
from builtins import next
from builtins import str
from builtins import range
import sys
import os
import shutil
import subprocess
import uuid
from argparse import ArgumentParser
import cv2
import numpy
import csv
from ..omero_basics import OMEROConnectionManager

OFFSET = 10
FONT = cv2.FONT_HERSHEY_SIMPLEX
DEFAULT_FONT_SIZE = 1
DEFAULT_DURATION = 1
TMP = '/tmp/'


def main(argv=sys.argv):

    # Configure argument parsing
    parser = ArgumentParser(description='''Produce images that can be encoded
                                           into a movie with ffmpeg''')
    parser.add_argument('image', type=int, help='Image ID')
    parser.add_argument('output', type=str,
                        help='Output directory (must exist)'),
    parser.add_argument('-l', '--labels', metavar='labels', type=str,
                        help='''Decorate images with labels from CSV file.
                                Format should be one row per cycle. The first
                                row is expected to be a header containing the
                                labels embedded in the image. Subsequent rows
                                represent the labels for each of the channels
                                in the same order as the header.'''),
    parser.add_argument('-p', '--placement', metavar='placement', type=str,
                        help='Channel name location (tl, bl, br, tr)')
    parser.add_argument('-f', '--font-size', metavar='font_size', type=int,
                        default=DEFAULT_FONT_SIZE,
                        help='''Relative font size
                                (Default: {})'''.format(DEFAULT_FONT_SIZE))
    parser.add_argument('-d', '--duration', metavar='duration', type=float,
                        default=DEFAULT_DURATION,
                        help='''Seconds per cycle
                                (Default: {})'''.format(DEFAULT_DURATION))
    parser.add_argument('-i', '--ignore', metavar='ignore', type=str,
                        help='''Ignore cycles, e.g. 0,1 (note no spaces). Note
                                that the first channel is zero, not one''')
    parser.add_argument('--tmp', metavar='tmp',
                        help='Temporary directory (Default: {})'.format(TMP))
    args = parser.parse_args()

    id = args.image
    output = args.output
    tmp = args.tmp or TMP

    # Make sure that ffmpeg is accessible
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.call(['ffmpeg', '-h'], stdout=devnull, stderr=devnull)

    except:
        sys.stderr.write('''ffmpeg not found, ensure that it is installed and
                            available on the path\n''')
        sys.exit(1)

    # Ensure that tmp directory exists and is a directory
    if not (os.path.exists(tmp) and
            os.path.isdir(tmp) and
            os.access(tmp, os.W_OK)):
        sys.stderr.write('''Temporary directory {} must exist, be a directory
                            and be writeable\n'''.format(tmp))

    # Expand any user directory in output directory
    output = os.path.expanduser(output)

    # Configure project directory location
    project = os.path.join(args.tmp or TMP,
                           'zmovie',
                           str(uuid.uuid1()))

    # Ensure that project directory does not exist
    if os.path.exists(project):
        sys.stderr.write(
            'Project directory {} exists. Failing for safety\n'.format(project)
        )
        sys.exit(1)

    # Placement requires labels
    if args.placement and not args.labels:
        sys.stderr.write('Placement requires a labels file to be specified\n')
        sys.exit(1)

    if args.placement and args.placement not in ['tl', 'bl', 'br', 'tr']:
        sys.stderr.write('Placement must be one of: tl, bl, br, tr\n')
        sys.exit(1)

    # Check output directory exists
    if not (os.path.exists(output) and os.path.isdir(output)):
        sys.stderr.write('Output directory {} must '
                         'exist\n'.format(output))
        sys.exit(1)

    conn_manager = OMEROConnectionManager()
    conn = conn_manager.connect()

    conn.SERVICE_OPTS.setOmeroGroup('-1')
    image = conn.getObject('Image', id)

    if not image:
        sys.stderr.write('Image {} not found or inaccessible!\n'.format(id))
        sys.exit(1)

    sizeZ = image.getSizeZ()

    channels = image.getChannels()

    # Check ignored cycles
    ignored_cycles = []
    if args.ignore:
        try:
            ignored_cycles = [int(c) for c in args.ignore.split(',')]
        except ValueError:
            sys.stderr.write('Ignored cycles must be integers\n')
            sys.exit(1)

        for c in ignored_cycles:
            if c >= sizeZ or c < 0:
                sys.stderr.write('''Ignored cycle ({}) beyond number of
                                    z-stacks in the image
                                    ({})\n'''.format(c, sizeZ))
                sys.exit(1)

    # Check labels
    labels = None
    if args.labels:

        with open(args.labels, 'rb') as csvfile:
            labels = [row for row in csv.DictReader(csvfile)]

        if len(labels) != sizeZ - len(ignored_cycles):
            sys.stderr.write('''Number of rows (1-per-cycle) in the CSV labels
                                file ({}) must equal the number of z-stacks in
                                the image ({}) after excluding ignored cycles
                                \n'''.format(len(labels),
                                             sizeZ - len(ignored_cycles)))
            sys.exit(1)

        for cycle in labels:
            if len(cycle) != len(channels):
                sys.stderr.write('''Number of columns (1-per-channel) in the
                                    CSV labels file ({}) must equal the number
                                    of channels in the image
                                    ()\n'''.format(len(cycle), len(channels)))
                sys.exit(1)

    # Create unique name project directory
    os.makedirs(project)

    if labels:
        labels_iter = iter(labels)

    for z in range(sizeZ):

        # Skip ignored cycles
        if z in ignored_cycles:
            continue

        rendered_image = image.renderImage(z, 0)
        plane = numpy.array(rendered_image)
        h, w, c = plane.shape

        RGB_plane = cv2.cvtColor(plane, cv2.COLOR_BGR2RGB)

        if labels:
            current_labels = next(labels_iter)
            for i, channel in enumerate(channels):
                label = current_labels[channel.getLabel()]
                color = channel.getColor()

                text_size = cv2.getTextSize(label, FONT,
                                            args.font_size, 1)[0]

                # Calculate text coordinate
                if args.placement is None or args.placement == 'tl':
                    text_coord = (
                        OFFSET,
                        (i + 1) * OFFSET + (i + 1) * text_size[1]
                    )
                elif args.placement == 'bl':
                    text_coord = (
                        OFFSET,
                        plane.shape[0] - (i + 1) * OFFSET - i * text_size[1]
                    )
                elif args.placement == 'br':
                    text_coord = (
                        plane.shape[1] - text_size[0] - OFFSET,
                        plane.shape[0] - (i + 1) * OFFSET - i * text_size[1]
                    )
                elif args.placement == 'tr':
                    text_coord = (
                        plane.shape[1] - text_size[0] - OFFSET,
                        (i + 1) * OFFSET + (i + 1) * text_size[1]
                    )

                cv2.putText(RGB_plane, label,
                            text_coord, FONT, args.font_size,
                            (
                                color.getBlue(),
                                color.getGreen(),
                                color.getRed()
                            ),
                            1, cv2.LINE_AA)

        # Write image
        cv2.imwrite(os.path.join(project, 'img_{}.jpg').format(z),
                    RGB_plane)

    # ffmpeg -framerate 1 -i color_img_%d.jpg -vcodec libx264 -crf 25 \
    #   -pix_fmt yuv420p -r 60 test.mp4
    try:
        subprocess.call(['ffmpeg', '-framerate', 1 / args.duration, '-y',
                         '-i', os.path.join(project, 'img_%d.jpg'), '-vcodec',
                         'libx264', '-crf', '25', '-pix_fmt', 'yuv420p',
                         '-r', '60',
                         os.path.join(output, '{}.mp4'.format(id))])
    except:
        sys.stderr.write('''Failed to process video with ffmpeg. Ensure it is
                            installed with the correct codecs\n''')
        sys.exit(1)

    # Cleanup
    shutil.rmtree(project)


if __name__ == '__main__':
    main()
