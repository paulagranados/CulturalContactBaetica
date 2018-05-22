# coding: utf-8

import google # Local file
import os, re
import rdflib
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
import unidecode
from urllib.parse import urlparse, parse_qs

import scrapers

# Define Utility RDF prefixes
crm = Namespace('http://erlangen-crm.org/current/')
DCTERMS = Namespace('http://purl.org/dc/terms/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')

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

def lookup_collections(label, graph):
	scrapers.JDA2RDF(graph)
	return None

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

def make_basic_entity(label, graph, type):
	"""Creates the generic triples for an entity ex novo"""
	base_uri = 'http://data.open.ac.uk/baetica/'
	lsani = unidecode.unidecode(label.strip().lower().replace(' ','_'))
	if   type == crm.E55_Type     : t = 'objtyp'
	elif type == crm.E57_Material : t = 'material'
	else: t = 'thing'
	subj = URIRef(base_uri + t + '/' + lsani)
	graph.add( ( subj, RDF.type, URIRef(type) ) )
	graph.add( ( subj, RDFS.label, Literal(label,lang='en') ) )
	return subj

def make_label(item, graph):
	l = ''
	if 'Culture Museum Atribution' in item and item['Culture Museum Atribution']:
		l += item['Culture Museum Atribution'].strip()
	if 'Material ' in item and item['Material ']:
		l += ' ' + item['Material '].strip()
	if 'Type' in item and item['Type']:
		l += ' ' + item['Type'].strip()
	else : l += ' ' + 'physical object'
	if 'Settlement ' in item and item['Settlement ']:
		l += ' from ' + item['Settlement '].strip()
	l = l.strip()
	return l

def make_uuid(item, graph):
	base_uri = "http://data.open.ac.uk/baetica/physical_object/"
	uuid = None
	if 'UUID' in item and item['UUID']:
		uuid = base_uri + 'arachne-' + '{num:04d}'.format(num=int(item['UUID']));
	# prefer Europeana over Arachne, and Arachne over museums
	if 'URI 3' in item and item['URI 3']:
		parsed = urlparse(item['URI 3'])		
		rexp = re.compile('/record/(\d+)/')
		matches = re.findall(rexp, parsed.path)
		if matches:
			ux = base_uri + 'ext-europeana/' + matches[0]
			if uuid : graph.add( ( URIRef(ux), OWL.sameAs, URIRef(uuid) ) )
			else : uuid = ux
	if 'URI' in item and item['URI']:
		# Extract the Arachne ID from the URI and reuse it
		# TODO: not the best way to do it, we should get the JSON data for that
		# object and get the IR attribute of that
		idd = item['URI'].rsplit('/', 1)[-1]
		if idd and idd.isdigit():
			ux = base_uri + 'ext-arachne/' + idd
			if uuid : graph.add( ( URIRef(ux), OWL.sameAs, URIRef(uuid) ) )
			else : uuid = ux
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
			ux = base_uri + ext + '/' + idd
			if uuid : graph.add( ( URIRef(ux), OWL.sameAs, URIRef(uuid) ) )
			else : uuid = ux
	return uuid

g = Graph() # The final RDF graph

# Get the Arachne data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
list = google.get_data('arachne', 'A:AZ')

# All the URIs we create for sculptures etc. will start like this
base_uri = "http://data.open.ac.uk/baetica/physical_object/ext-arachne/"

for index, item in enumerate(list):
	subj = make_uuid(item, g)
	if subj :
		us = URIRef(subj)
		g.add( ( us, RDF.type, URIRef('http://www.cidoc-crm.org/cidoc-crm/E24_Physical_Man-Made_Thing') ) )
		if 'Description' in item and item['Description']:
			g.add( ( us, DCTERMS.description, Literal(item['Description'].strip(),lang='en') ) )
		# Look for an exact match on the material (using the Eagle vocabulary)
		if 'Material ' in item and item['Material ']:
			match = lookup_eagle(item['Material '].strip(), 'material', 'https://www.eagle-network.eu/voc/material/')
			if match: um = match
			else: um = make_basic_entity(t, g, crm.E57_Material)
			g.add( ( us, crm.P45_consists_of, URIRef(um) ) )
		# Create the "location" predicate when there is a Pleiades URI
		if 'Pleiades URI' in item and item['Pleiades URI']:
			g.add( ( us, geo.location, URIRef(item['Pleiades URI'].strip()) ) )
		# Look for an exact match on the object type (using the Eagle vocabulary)
		if 'Type' in item and item['Type']:
			t = item['Type'].strip()
			match = lookup_eagle(item['Type'].strip(), 'object_type', 'https://www.eagle-network.eu/voc/objtyp/')
			if match: um = match
			else: um = make_basic_entity(t, g, crm.E55_Type)
			g.add( ( us, crm.P2_has_type, URIRef(um) ) )
		l = make_label(item, g)
		if l:
			g.add( ( us, RDFS.label, Literal(l,lang='en') ) )
		else:
			print('[WARN] Row ' + str(index + 2) + ' failed to generate a label.')
	else:
		print('[WARN] Row ' + str(index + 2) + ' failed to generate a UUID.')
			
# Print the graph in Turtle format to screen (with nice prefixes)
g.namespace_manager.bind('crm', URIRef('http://www.cidoc-crm.org/cidoc-crm/'))
g.namespace_manager.bind('geo', URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#'))

# ... to a file 'out/arachne.ttl' (will create the 'out' directory if missing)
dir = 'out'
if not os.path.exists(dir):
    os.makedirs(dir)
# Note: it will overwrite the existing Turtle file!
path = os.path.join(dir, 'arachne.ttl')
g.serialize(destination=path, format='turtle')
print('DONE. ' + str(len(g)) + ' triples written to ' + path)

# Uncomment the last line to print to screen instead of file
# ... but don't forget that the other messages printed earlier will get in the way!
# print(g.serialize(format='turtle').decode('utf8'))
