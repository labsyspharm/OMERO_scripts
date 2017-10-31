#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
import uuid
from argparse import ArgumentParser
import cv2
import numpy
from ..omero_basics import OMEROConnectionManager

OFFSET = 10
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SIZE = 0.5
TMP = '/tmp/'


def main(argv=sys.argv):

    # Configure argument parsing
    parser = ArgumentParser(description='Produce images that can be encoded'
                            'into a movie with ffmpeg')
    parser.add_argument('image', type=int, help='Image ID')
    parser.add_argument('output', type=str,
                        help='Output directory (must exist)'),
    parser.add_argument('-l', '--label', action='store_const', const=True,
                        default=False,
                        help='Decorate images with label'),
    parser.add_argument('-p', '--placement', metavar='placement',
                        help='Channel name location (tl, bl, br, tr)')
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
        print '''ffmpeg not found, ensure that it is installed and available
                 on the path'''
        sys.exit(1)

    # Ensure that tmp directory exists and is a directory
    if not (os.path.exists(tmp) and
            os.path.isdir(tmp) and
            os.access(tmp, os.W_OK)):
        print '''Temporary directory {} must exist, be a directory and be
                 writeable'''.format(tmp)

    # Expand any user directory in output directory
    output = os.path.expanduser(output)

    # Configure project directory location
    project = os.path.join(args.tmp or TMP,
                           'zmovie',
                           str(uuid.uuid1()))

    # Ensure that project directory does not exist
    if os.path.exists(project):
        print 'Project directory {} exists. Failing for safety'.format(project)
        sys.exit(1)

    # Create unique name project directory
    os.makedirs(project)

    # Placement implies label
    if args.label or args.placement:
        label = True
    else:
        label = False

    if args.placement and args.placement not in ['tl', 'bl', 'br', 'tr']:
        sys.stderr.write('Placement must be one of: tl, bl, br, tr')
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
        sys.stderr.write('Image {} not found or inaccessible\n!'.format(id))
        sys.exit(1)

    sizeZ = image.getSizeZ()

    channels = image.getChannels()

    for z in xrange(sizeZ):
        rendered_image = image.renderImage(z, 0)
        plane = numpy.array(rendered_image)
        h, w, c = plane.shape

        RGB_plane = cv2.cvtColor(plane, cv2.COLOR_BGR2RGB)

        if label:

            for i, channel in enumerate(channels):
                text_size = cv2.getTextSize(channel.getLabel(), FONT,
                                            FONT_SIZE, 1)[0]

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

                cv2.putText(RGB_plane, channel.getLabel(), text_coord, FONT,
                            FONT_SIZE, channel.getColor().getRGB(), 2,
                            cv2.LINE_AA)

        # Write image
        cv2.imwrite(os.path.join(project, 'img_{}.jpg').format(z),
                    RGB_plane)

    # ffmpeg -framerate 1 -i color_img_%d.jpg -vcodec libx264 -crf 25 \
    #   -pix_fmt yuv420p -r 60 test.mp4
    try:
        subprocess.call(['ffmpeg', '-framerate', '1', '-y', '-i',
                         os.path.join(project, 'img_%d.jpg'), '-vcodec',
                         'libx264', '-crf', '25', '-pix_fmt', 'yuv420p',
                         '-r', '60', '{}.mp4'.format(id)])
    except:
        print '''Failed to process video with ffmpeg. Ensure it is installed
                 with the correct codecs'''
        sys.exit(1)

    # Cleanup
    shutil.rmtree(project)


if __name__ == '__main__':
    main()
