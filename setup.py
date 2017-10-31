import os
from ConfigParser import ConfigParser
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

requires = [
    'numpy>=1.11.1',
    'opencv-python>=3.3.0.10',
    'colour>=0.1.4',
    'PyYAML>=3.12'
]


def read_version():
    config = ConfigParser()
    config.read('setup.cfg')
    return config.get('metadata', 'version')


VERSION = read_version()
DESCRIPTION = 'OMERO scripts'
AUTHOR = 'D.P.W. Russell'
LICENSE = 'AGPL-3.0'
HOMEPAGE = 'https://github.com/sorgerlab/OMERO_scripts'

setup(
    name='omero-scripts',
    version=VERSION,
    description=DESCRIPTION,
    long_description=README,
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'zmovie=omero_scripts.analysis.zmovie:main',
            'list_all_projects_with_datasets=omero_scripts.queries.list_all_projects_with_datasets:main',
            'list_plate_images=omero_scripts.queries.list_plate_images:main',
            'list_project_images= mero_scripts.queries.list_project_images:main',
            'list_screen_images=omero_scripts.queries.list_screen_images:main',
            'list_screen_plates=omero_scripts.queries.list_screen_plates:main',
            'csv2yaml=omero_scripts.conversion.csv2yaml:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering :: Visualization'
    ],
    author=AUTHOR,
    author_email='douglas_russell@hms.harvard.edu',
    license=LICENSE,
    url=HOMEPAGE,
    download_url='%s/archive/v%s.tar.gz' % (HOMEPAGE, VERSION),
    keywords=['omero', 'scripts', 'microscopy'],
    zip_safe=False,
)
