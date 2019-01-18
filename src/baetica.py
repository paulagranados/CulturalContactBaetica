#!/usr/bin/env python

import argparse
import importlib, importlib.util

parser = argparse.ArgumentParser(description='Run one or more linked data extractors for Cultural Contact Baetica.')
parser.add_argument('sources', metavar='S', nargs='+',
                   help='the name of a data source (there must be a Python module with that name in the \'extractors\' package)')
                   
args = parser.parse_args()
if args.sources:
	print('Looking for the following extractors to run: ' + str(args.sources))
	for src in vars(args)['sources']:
		spec = importlib.util.find_spec('extractors.' + src)
		if spec is None : print('[ERROR] module \'' + src + '\' not found, did you forget to drop a \'' + src + '.py\' inside the \'extractors\' package?')
		else : importlib.import_module('extractors.' + src)
