# coding: utf-8

import os, re
from json import JSONDecodeError
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, OWL, RDF, RDFS, XSD
from rdflib.namespace import DCTERMS, SKOS
import unidecode
from urllib.parse import urlparse, parse_qs
from urllib.error import HTTPError, URLError

import commons.rdf as crdf
import google # Local module

print('Running Settlements Data extractor (from Google sheet)...')

# Define utility RDF prefixes, so you can just use 'crm' to create any
# URIRef for any class or property in CIDOC-CRM, for example.
CuCoO = Namespace('http://www.semanticweb.org/paulagranadosgarcia/CuCoO/')
crm = Namespace('http://erlangen-crm.org/current/')
rdf = Namespace ('http://www.w3.org/1999/02/22-rdf-syntax-ns#') # for containers
skos = Namespace ('http://www.w3.org/2004/02/skos/core#')
spatial = Namespace ('http://geovocab.org/spatial#')
owl = Namespace ("http://www.w3.org/2002/07/owl#") 


# These are the URIs of the RDF vocabularies that we can load
vocabs = {
    'nomisma': 'http://nomisma.org/ontology.rdf',
    'CuCoO': 'https://raw.githubusercontent.com/paulagranados/CuCoO/master/CuCoO.owl'
}
# Load the necessary vocabularies so we can query them locally
# (Nomisma is only here as an example)
g_nomisma = Graph()
g_nomisma.parse(vocabs['nomisma'], format="xml")
g_CuCoO = Graph ()
g_CuCoO.parse (vocabs ['CuCoO'], format="xml")

# Create the universal identifier (must be a URIRef)

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
	# All the URIs we create for Settlements will start like this
	base_uri = "http://data.open.ac.uk/baetica/settlement/"
	uuid = None
	# WARN: note the space after Settlement : it is there becase there is one
	# on the spreadsheet. DO NOT CHANGE IT unless you change it on the spreadsheet first!
	if 'Settlement' in item and item['Settlement'] and 'ID' in item and item['ID'] :
		locn = item['Settlement'].strip()
		id = item['ID'].strip()
		if locn in uricache and id in uricache[locn] : 
			print('[WARN] there is already an item for Settlement {0} and ID {1} : {2}'.format(locn, id, uricache[locn][id]))
		else:
			if not locn in uricache : uricache[locn] = {}
			# This is the part you were missing: you need to concatenate the elements
			# that you want and assign the result to uuid, otherwise it will always be null!
			uuid = base_uri + locn.lower().replace(' ','_') + '/' + id
			uricache[locn][id] = uuid
	else: print('[WARN] row ' + str(index + 2) + ': Could not find suitable UUID to make an URI from.')
	return uuid
	
g = Graph() # This will contain the final RDF graph

# Get the Settlements data from the online Google Sheet.
print('Slicing Google sheet SettlementsData to range A:BZ ...')
list = google.get_data('SettlementsData', 'A:BZ')
print('Done. Got {:d} elements'.format(len(list)))

# Now process the rows in the spreadsheet
for i, item in enumerate(list):
	subj = make_uuid(item, g, i)
	if subj :
		subj = URIRef(subj)
		label = ''
		
		# Add some types (for rdf:type and other taxonomical properties)
		g.add( (subj, RDF.type, URIRef(CuCoO.Settlement) ) )
		
		# Make the rdfs:label out of what is in the Settlement column
		if 'Settlement' in item and item['Settlement'] :
			locn = item['Settlement'].strip()
			label = locn
			g.add( ( subj, RDFS.label, Literal(label, lang='en') ) )
			
		#Make labels
		if 'Description' in item and item['Description'] :
			desc = item['Description'].strip()
			g.add( ( subj, RDFS.comment, Literal(desc, lang='en') ) )
						
		if 'Ethnicity_A1' in item and item['Ethnicity_A1'] :
			desc = item['Ethnicity_A1'].strip()
			g.add( ( subj, CuCoO.HasEthnicity,  Literal(desc, lang='en') ) )
			
		if 'Ethnicity_B1' in item and item ['Ethnicity_B1'] :
		    desc = item['Ethnicity_B1'].strip()
		    g.add( (subj, CuCoO.HasEthnicity, Literal(desc,lang='en') ) ) 
  
		if 'Ethnicity_C1' in item and item ['Ethnicity_C1'] :
		    desc = item['Ethnicity_C1'].strip()
		    g.add( (subj, CuCoO.HasEthnicity, Literal(desc,lang='en') ) )
		
		#Reference: 
		
		if 'CVB' in item and item['CVB'] :
			desc = item['CVB'].strip()
			g.add( (subj, RDFS.seeAlso, URIRef(desc) ) ) 
		
		if 'IAPH' in item and item['IAPH'] :
		    desc = item['IAPH'].strip()
		    g.add( (subj, RDFS.seeAlso, URIRef(desc) ) ) 
		    
			
#########################
#### POST-PROCESSING ####
#########################

# Perform any external lookups if needed. 
# You can put any resulting data alignments into 'g'

#########################
######## OUTPUT #########
#########################

# Print the graph in Turtle format (with nice prefixes)
g.namespace_manager.bind('crm', crm)
g.namespace_manager.bind('cucoo', CuCoO)
# Add as many prefix bindings as the namespaces of your data 

# ... to a file 'out/settlements.ttl' (will create the 'out' directory if missing)
dir = 'out'
if not os.path.exists(dir):
    os.makedirs(dir)
# Note: it will overwrite the existing Turtle file!
path = os.path.join(dir, 'settlements.ttl')
g.serialize(destination=path, format='turtle')
print('DONE. ' + str(len(g)) + ' triples written to ' + path)

# Uncomment the last line to print to screen instead of file
# ... but don't forget that the other messages printed earlier will get in the way!
# So you will have to remove every line of code that prints status messages
# print(g.serialize(format='turtle').decode('utf8'))
    
    
   
    

