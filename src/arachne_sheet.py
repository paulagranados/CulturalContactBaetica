# coding: utf-8

import google # Local file

import rdflib
from rdflib import Graph, Namespace, URIRef
import re
from urllib.parse import urlparse, parse_qs

# Define Utility RDF prefixes
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')

vocabs = {
    'material': 'https://www.eagle-network.eu/voc/material.rdf', 
    'object_type': 'https://www.eagle-network.eu/voc/objtyp.rdf'
}

# Load the EAGLE SKOS vocabularies so we can query them locally
g_material = Graph()
g_material.parse(vocabs['material'], format="xml")
g_object_type = Graph()
g_object_type.parse(vocabs['object_type'], format="xml")
# Data structures to cache successful and failed matches
map_material = { '_miss_' : [] }
map_object_type = { '_miss_' : [] }

def lookup_eagle(label, gr, type):
	"""Tries to find a string match for a given label in a selected
	EAGLE controlled vocabulary."""
	# First check if a cached result exists
	map = globals()['map_' + gr]
	if label in map: return map[label]
	if label in map['_miss_']: return None
	# If not, do a local SPARQL query on the SKOS vocabulary 
	graph = globals()['g_' + gr]
	q = """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?x
WHERE {
   ?x skos:inScheme <""" + type + """>
    ; skos:altLabel ?l FILTER( lcase(str(?l)) = '""" + label.lower() + """' )
}"""
	qres = graph.query(q)
	# Update the cache accordingly
	for row in qres:
		map[label] = row[0]
		return row[0]
	map['_miss_'].append(label)
	return None

def make_uuid(item, graph):
	base_uri = "http://data.open.ac.uk/baetica/physical_object/"
	uuid = None
	# prefer Europeana over Arachne, and Arachne over museums
	if 'URI 3' in item and item['URI 3']:
		parsed = urlparse(item['URI 3'])		
		rexp = re.compile('/record/(\d+)/')
		matches = re.findall(rexp, parsed.path)
		if matches : uuid = base_uri + 'ext-europeana/' + matches[0]
	if 'URI' in item and item['URI']:
		# Extract the Arachne ID from the URI and reuse it
		# TODO: not the best way to do it, we should get the JSON data for that
		# object and get the IR attribute of that
		idd = item['URI'].rsplit('/', 1)[-1]
		if idd and idd.isdigit():
			uri = base_uri + 'ext-arachne/' + idd
			if uuid : graph.add( ( URIRef(uuid), rdfs.seeAlso, URIRef(uri) ) )
			else : uuid = uri
	if 'URI 2' in item and item['URI 2']:
		idd = None
		ext = None
		parsed = urlparse(item['URI 2'])
		if 'www.juntadeandalucia.es' == parsed.netloc :
			pqs = parse_qs(parsed.query)
			if 'ninv' in pqs: 
				idd = pqs['ninv'][0]
				ext = 'ext-museosdeandalucia'
		elif 'ceres.mcu.es' == parsed.netloc :
			pqs = parse_qs(parsed.query)
			if 'inventary' in pqs :
				idd = pqs['inventary'][0]
				ext = 'ext-ceres'
		if idd and ext:
			uri = base_uri + ext + '/' + idd
			if uuid : graph.add( ( URIRef(uuid), rdfs.seeAlso, URIRef(uri) ) )
			else : uuid = uri
	return uuid

g = Graph() # The final RDF graph

# Get the Arachne data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
list = google.get_data('arachne', 'A:AF')

# All the URIs we create for sculptures etc. will start like this
base_uri = "http://data.open.ac.uk/baetica/physical_object/ext-arachne/"

for item in list:
	subj = make_uuid(item, g)
	if subj : 
		g.add( ( URIRef(subj), rdf.type, crm.E24 ) )
		# Create the "location" predicate when there is a Pleiades URI
		if 'Pleiades URI' in item and item['Pleiades URI']:
			g.add( ( URIRef(subj), geo.location, URIRef(item['Pleiades URI']) ) )
		# Look for an exact match on the material (using the Eagle vocabulary)
		if 'Material ' in item and item['Material ']:
			match = lookup_eagle(item['Material '], 'material', 'https://www.eagle-network.eu/voc/material/')
			if match: g.add( ( URIRef(subj), crm.P45, URIRef(match) ) )
		# Look for an exact match on the object type (using the Eagle vocabulary)
		if 'Type' in item and item['Type']:
			match = lookup_eagle(item['Type'], 'object_type', 'https://www.eagle-network.eu/voc/objtyp/')
			if match: g.add( ( URIRef(subj), crm.P2, URIRef(match) ) )
			
# Print the graph in Turtle format to screen (with nice prefixes)
g.namespace_manager.bind('crm', URIRef('http://www.cidoc-crm.org/cidoc-crm/'))
g.namespace_manager.bind('geo', URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#'))
print(g.serialize(format='turtle').decode('utf8'))
