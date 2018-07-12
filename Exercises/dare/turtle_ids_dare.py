#Go to the DARE API
#Extract the JSON
#get the IDs for the places
#get the URIs from the IDs
#get the RDF from the URIs

import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen
import requests 
import json
from pprint import pprint

with urlopen('http://dare.ht.lu.se/api/geojson.php?cc=Es') as url:
    http_info = url.info()
    data = url.read().decode(http_info.get_content_charset())
dare_data = json.loads(data)
#pprint(dare_data['features'])
for each in dare_data['features']:
    print('http://dare.ht.lu.se/places/'+each['properties']['id']+'.ttl')