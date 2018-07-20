# -*- coding: utf-8 -*-

import requests
import pprint

def annotations( text, types=None ) :
	svc =  "http://api.dbpedia-spotlight.org/en/annotate?"
	payload = { 'confidence' : 0.5, 'text': text, 'types': ','.join(types) }
	r = requests.get(svc, params=payload, headers={'Accept': 'application/json'})
	return r.json()


