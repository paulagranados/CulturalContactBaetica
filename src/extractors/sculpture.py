# coding: utf-8

import os, re
import rdflib
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS
import unidecode
from urllib.parse import urlparse, parse_qs

import commons.rdf as crdf
import google # Local module
from scrapers.jda import JDA2RDF # Local module

print('Running sculpture extractor (from Google sheet)...\n')

# Define Utility RDF prefixes
crm = Namespace('http://erlangen-crm.org/current/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')
CuCoO = Namespace('http://www.semanticweb.org/paulagranadosgarcia/CuCoO/')

vocabs = {
    'material': 'https://www.eagle-network.eu/voc/material.rdf', 
    'object_type': 'https://www.eagle-network.eu/voc/objtyp.rdf',
    'CuCoO': 'https://raw.githubusercontent.com/paulagranados/CuCoO/master/CuCoO.owl'
}

# Load the EAGLE SKOS vocabularies so we can query them locally
g_material = Graph()
g_material.parse(vocabs['material'], format="xml")
g_object_type = Graph()
g_object_type.parse(vocabs['object_type'], format="xml")
# Data structures to cache successful and failed matches
map_material = { '_miss_' : [] }
map_object_type = { '_miss_' : [] }

def lookup_collections(url, graph):
	domain = '{u.netloc}'.format(u=urlparse(url))
	if domain == 'www.juntadeandalucia.es' : scr = JDA2RDF(graph)
	else : scr = None
	if scr : scr.build( scr.scrape(url) )

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
    ; skos:prefLabel|skos:altLabel ?l FILTER( lcase(str(?l)) = '""" + label.lower() + """' )
}"""
	qres = graph.query(q)
	# Update the cache accordingly
	for row in qres:
		map[label] = row[0]
		return row[0]
	print('[WARN] Could not find a match for label "' + label + '" in EAGLE vocabulary <' + type + '>')
	map['_miss_'].append(label)
	return None

uricache = {}
def make_uuid(item, graph, index = -1):
	'''
	Creates the universal unique identifier (UUID) for the main entity 
	represented by a given row in the spreadsheet. Returns a URIRef.
	Use whatever rows contribute to the uniqueness of this entity (for 
	example in Nomisma it was a combination of ID and Series).
	
	:param item: the row in the spreadsheet
	:param graph: the RDF graph where all the data are being stored
	:param index: the row number you are making the ID for
	'''
	# All the URIs we create for Sculpture will start like this
	base_uri = "http://data.open.ac.uk/erub/sculpture/"
	uuid = None
	# WARN: note the space after Settlement : it is there becase there is one
	# on the spreadsheet. DO NOT CHANGE IT unless you change it on the spreadsheet first!
	if 'f' in item and item['f'] and 'ID' in item and item['ID'] :
		locn = item['f'].strip()
		id = item['ID'].strip()
		if locn in uricache and id in uricache[locn] : 
			print('[WARN] there is already an item for Sculpture {0} and ID {1} : {2}'.format(locn, id, uricache[locn][id]))
		else:
			if not locn in uricache : uricache[locn] = {}
			# This is the part you were missing: you need to concatenate the elements
			# that you want and assign the result to uuid, otherwise it will always be null!
			uuid = base_uri + locn.lower().replace(' ','_') + '/' + id.lower()
			uricache[locn][id] = uuid
	else: print('[WARN] row ' + str(index + 2) + ': Could not find suitable UUID to make an URI from.')
	return uuid
g = Graph() # This will contain the final RDF graph

print('Slicing Google sheet SculptureData to range A:AZ ...')
list = google.get_data('SculptureData', 'A:AZ')
print('Done. Got {:d} elements'.format(len(list)))
# Now process the rows in the spreadsheet
for i, item in enumerate(list):
	subj = make_uuid(item, g, i)
	if subj :
		subj = URIRef(subj)
		label = ''

		# Make labels
		if 'Description' in item and item['Description']:
			g.add( ( us, DCTERMS.description, Literal(item['Description'].strip(),lang='en') ) )
		if 'Carving' in item and item ['Carving']:
		    g.add( (us, CuCoO.hasCarving,  Literal(item['Carving'].strip(), lang='en') ) ) 
		# Look for an exact match on the material (using the Eagle vocabulary)
		if 'Material ' in item and item['Material ']:
			match = lookup_eagle(item['Material '].strip(), 'material', 'https://www.eagle-network.eu/voc/material/')
			if match: um = match
			else: um = crdf.make_basic_entity(t, g, crm.E57_Material)
			g.add( ( us, cucoo.hasMaterial, URIRef(um) ) )
		# Create the "location" predicate when there is a Pleiades URI
		if 'Pleiades URI' in item and item['Pleiades URI']:
			g.add( ( us, geo.location, URIRef(item['Pleiades URI'].strip()) ) 
		if 'Technique' in item and item ['Technique']:
			g.add( ( us, cucoo.hasTechnique, Literal(item['Technique'].strip(), lang='en') ) ) 
					
# Print the graph in Turtle format to screen (with nice prefixes)
 g.namespace_manager.bind('crm', URIRef('http://www.cidoc-crm.org/cidoc-crm/'))
 g.namespace_manager.bind('geo', URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#'))
 g.namespace_manager.bind('cucoo', CuCoO)

# ... to a file 'out/sculpture.ttl' (will create the 'out' directory if missing)
dir = 'out'
if not os.path.exists(dir):
    os.makedirs(dir)
# Note: it will overwrite the existing Turtle file!
path = os.path.join(dir, 'sculpture.ttl')
g.serialize(destination=path, format='turtle')
print('DONE. ' + str(len(g)) + ' triples written to ' + path)

# Uncomment the last line to print to screen instead of file
# ... but don't forget that the other messages printed earlier will get in the way!
# print(g.serialize(format='turtle').decode('utf8'))
