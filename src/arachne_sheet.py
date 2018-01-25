# coding: utf-8

import google # Local file

import rdflib
from rdflib import Graph, Namespace, URIRef

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
   ?x skos:inScheme <"""+type+""">
    ; skos:altLabel ?l FILTER( lcase(str(?l)) = '"""+label+"""' )
}"""
	qres = graph.query(q)
	# Update the cache accordingly
	for row in qres:
		map[label] = row[0]
		return row[0]
	map['_miss_'].append(label)
	return None

# Define Utility RDF prefixes
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

g = Graph() # The final RDF graph

# Get the Arachne data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
list = google.get_data('arachne', 'A:AF')

# All the URIs we create for sculptures etc. will start like this
base_uri = "http://data.open.ac.uk/baetica/physical_object/ext-arachne/"

for item in list:
	subj = ''
	if 'URI' in item and item['URI']:
		# Extract the Arachne ID from the URI and reuse it
		# TODO: not the best way to do it, we should get the JSON data for that
		# object and get the IR attribute of that
		id = item['URI'].rsplit('/', 1)[-1]
		if id.isdigit():
			subj = base_uri + id
			g.add( ( URIRef(subj), rdf.type, crm.E24 ) )
	# Create the "location" predicate when there is a Pleiades URI
	if subj and 'Pleiades URI' in item and item['Pleiades URI']:
		g.add( ( URIRef(subj), geo.location, URIRef(item['Pleiades URI']) ) )
	# Look for an exact match on the material (using the Eagle vocabulary)
	if subj and 'Material ' in item and item['Material ']:
		match = lookup_eagle(item['Material '], 'material', 'https://www.eagle-network.eu/voc/material/')
		if match:
			g.add( ( URIRef(subj), crm.P45, URIRef(match) ) )
	# Look for an exact match on the object type (using the Eagle vocabulary)
	if subj and 'Type' in item and item['Type']:
		match = lookup_eagle(item['Type'], 'object_type', 'https://www.eagle-network.eu/voc/objtyp/')
		if match:
			g.add( ( URIRef(subj), crm.P2, URIRef(match) ) )
			
# Print the graph in Turtle format to screen (with nice prefixes)
g.namespace_manager.bind('crm', URIRef('http://www.cidoc-crm.org/cidoc-crm/'))
g.namespace_manager.bind('geo', URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#'))
print(g.serialize(format='turtle').decode('utf8'))
