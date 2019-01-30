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
			g.add( ( subj, CuCoO.hasEthnicity,  Literal(desc, lang='en') ) )
			
		if 'Ethnicity_B1' in item and item['Ethnicity_B1'] :
			desc = item['Ethnicity_B1'].strip()
			g.add( (subj, CuCoO.hasEthnicity, Literal(desc,lang='en') ) ) 
			
		if 'Ethnicity_C1' in item and item['Ethnicity_C1'] :
			desc = item['Ethnicity_C1'].strip()
			g.add( (subj, CuCoO.hasEthnicity, Literal(desc,lang='en') ) )
			
		if 'Conventus' in item and item['Conventus'] :
			desc= item['Conventus'].strip()
			desc= URIRef('http://data.open.ac.uk/baetica/administrative_region/' + desc)
			g.add ( (subj, CuCoO.hasConventus, desc) )
			
		#Creating a ternary relationship between the settlements and the dates when they received a specific legal status.
		#Osuna    has_Legal_Status    legalstatus_osuna_12345 .
        #legalstatus_osuna_12345    a    sit:TimeIndexedSituation
        #;    sit:atTime    "-44"^^xsd:gYear
        #;    has_status_definition    Colonia

		#if 'Settlement' in item and item ['Settlement'] :
		#	set = item['Settlement'].strip()
		#	id = item['ID'].strip()
		#	label = ('LegalStatus_') + set + ('_') + id
		#	g.add ( ( subj, CuCoO.hasLegalStatus, Literal(label, lang='en') ) 
		#	time = item['sit.TimeIndexedSituation'].strip()
		#	g.add ( (label, RDFS.label, Literal(time))
		#	if 'YearA' in tem and item ['YearA'] :
		#		year = item['YearA'].strip()
		#		g.add ( ( sit, sit.atTime, int(year) )
		#		if 'LegalStatusA' in item and item ['LegalStatusA'] : 
		#			status = item['LegalStatusA'].strip()
		#			g.add ( (definition, CuCoO.hasStatusDefinition, Literal(status, lang='n') )
		
		#Linking:
		
		if 'R-Province1' in item and item ['R-Province1'] :
			prov1 = item['R-Province1'].strip()
			prov1_u = URIRef('http://data.open.ac.uk/baetica/pre-Augustean_province/Hispania_' + prov1)
			prov1_dbp = URIRef('http://dbpedia.org/resource/Hispania_' + prov1)
			g.add ( (subj, CuCoO.hasProvince, prov1_u) )
			g.add ( (prov1_u, skos.closeMatch, prov1_dbp) ) 
			
		if 'R-Province2' in item and item ['R-Province2'] :
			prov2 = item['R-Province2'].strip()
			prov2_u = URIRef('http://data.open.ac.uk/baetica/post-Augustean_province/Hispania_' + prov2)
			prov2_dbp = URIRef('http://dbpedia.org/resource/Hispania_'+ prov2)
			g.add ( (subj, CuCoO.hasProvince, prov2_u) )
			#if 'Lusitania' not in prov2_dbp : 
			g.add ( (prov2_u, skos.closeMatch, prov2_dbp) )
			
		#Different names for the settlements along time. 
			
		if 'Name1' in item and item ['Name1'] :
			name1 = item['Name1'].strip()
			name1_u = URIRef('http://data.open.ac.uk/baetica/settlement_name/' + name1)
			g.add ( (subj, CuCoO.hasName, name1_u) )
			#if 'Name1_Pleaides_URI' in item and item ['Name1_Pleiades_URI'] :
			#	name1_p = item['Name1_Pleaides_URI']
			#	g.add ( (name1_u, skos.closeMatch, URIRef(name1_p) ) )
			
		if 'Name2' in item and item ['Name2'] :
			name2 = item['Name2'].strip()
			name2_u = URIRef('http://data.open.ac.uk/baetica/settlement_name/' + name2)
			g.add ( (subj, CuCoO.hasName, name2_u) )
			
		if 'Name3' in item and item ['Name3'] :
			name3 = item['Name3'].strip()
			name3_u = URIRef('http://data.open.ac.uk/baetica/settlement_name/' + name3)
			g.add ( (subj, CuCoO.hasName, name3_u) )
			
		if 'Name4' in item and item ['Name4'] :
			name4 = item['Name4'].strip()
			name4_u = URIRef('http://data.open.ac.uk/baetica/settlement_name/' + name4)
			g.add ( (subj, CuCoO.hasName, name4_u) )
			
		if 'Current_name' in item and item ['Current_name'] :
			current_name = item['Current_name']
			current_name_u = URIRef('http://data.open.ac.uk/baetica/settlement_name/' + current_name)
			g.add ( ( subj, CuCoO.hasName, Literal(current_name, lang ='es') )
			
		#Alignment in order of compatibility: 
			
		if 'IAPH' in item and item['IAPH'] :
			desc = item['IAPH'].strip()
			g.add( (subj, RDFS.seeAlso, URIRef(desc) ) )
			
		if 'CVB' in tem and item['CVB'] :
			desc = item['CVB'].strip()
			g.add( (subj, RDFS.seeAslo, URIRef(desc) ) )
			
		if 'Wikipedia' in item and item['Wikipedia'] :
			desc = item['Wikipedia'].strip()
			g.add( (subj, RDFS.seeAlso, URIRef(desc) ) )
			
		if 'Wikidata' in item and item['Wikidata'] :
			desc = item['Wikidata'].strip()
			g.add( (subj, skos.closeMatch, URIRef(desc) ) )
			
		if 'TM' in item and item['TM'] :
			desc = item['TM'].strip()
			g.add( (subj, skos.exactMatch, URIRef(desc) ) ) 
			
		if 'DARE' in item and item['DARE'] :
			desc = item['DARE'].strip()
			g.add( (subj, skos.exactMatch, URIRef(desc) ) )
		
		if 'VICI' in item and item['VICI'] :
			desc = item['VICI'].strip()
			g.add( (subj, skos.exactMatch, URIRef(desc) ) ) 
			
		if 'Pleiades' in item and item['Pleiades'] :
			desc = item['Pleiades'].strip()
			g.add( (subj, skos.exactMatch, URIRef(desc) ) ) 
			
			
			
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
g.namespace_manager.bind('skos', skos)
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
    
    
   
    

