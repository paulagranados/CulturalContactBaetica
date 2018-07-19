#!/usr/bin/env python

from setuptools import setup

setup(name='Cultural Contact Baetica',
      version='0.2',
      description='Python Distribution Utilities',
      author='Paula Granados Garcia',
      author_email='',
      url='https://github.com/paulagranados/CulturalContactBaetica',
      install_requires=[
         'bs4',
         'google-api-python-client',
         'oauth2client',
         'rdflib',
         'requests',
         'unidecode',
         'SPARQLWrapper'
      ],
)
