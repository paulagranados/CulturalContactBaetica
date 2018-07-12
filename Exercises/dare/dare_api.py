#Go to the DARE API
#Extract the JSON
#get the IDs for the places
#get the URIs from the IDs
#get the RDF from the URIs

import urllib.request, urllib.parse, urllib.error
import requests 
import json

dare = urllib.request.urlopen ('http://dare.ht.lu.se/api/geojson.php?cc=Es')
data = dare.read().decode()
	print('Retrieved', len(data), 'characters')
	

	


