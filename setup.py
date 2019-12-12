#!/usr/bin/env python

from setuptools import setup, find_packages

__version__ = "0.2"


def _read(doc):
    return open(doc, 'rb').read()


setup(
    name="hbz.cdntools",
    version=__version__,
    author="Peter Reimer",
    author_email="reimer@hbz-nrw.de",
    description="Creates a list of external and local css and js files inluded in a website.",
    long_description=_read('README.rst').decode('utf-8'),
    install_requires=[
        'setuptools',
        'argparse',
        'requests',
        'beautifulsoup4'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    license="DFSL",
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['hbz', 'hbz.cdntools'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'cdnparse=hbz.cdntools.parse:main',
        ]
    },
)
