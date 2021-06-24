#!/usr/bin/env python

from setuptools import setup, find_packages
from NwalaTextUtils import __version__

desc = """Collection of functions for processing text"""


setup(
    name='NwalaTextUtils',
    version=__version__,
    description=desc,
    long_description='See: https://github.com/oduwsdl/NwalaTextUtils/',
    author='Alexander C. Nwala',
    author_email='alexandernwala@gmail.com',
    url='https://github.com/oduwsdl/NwalaTextUtils/',
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    install_requires=[
       'beautifulsoup4',
       'boilerpy3>=1.0.4',
       'requests',
       'tldextract'
    ]
)
