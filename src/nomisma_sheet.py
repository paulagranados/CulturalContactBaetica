# This is not a Google library, it's our own wrapper for the Google Web API
import google
import os, re
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from urllib.parse import urlparse, parse_qs

# Define Utility RDF prefixes
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
dct = Namespace ('http://purl.org/dc/terms/') 
geo = Namespace ('http://www.w3.org/2003/01/geo/wgs84_pos#') 
osgeo = Namespace ('http://data.ordnancesurvey.co.uk/ontology/geometry/') 
nmo = Namespace ('http://nomisma.org/ontology#') 
nm = Namespace ('http://nomisma.org/id/') 
rdf = Namespace ('http://www.w3.org/1999/02/22-rdf-syntax-ns#') 
rdfs = Namespace ('http://www.w3.org/2000/01/rdf-schema#')
rs = Namespace ('http://www.researchspace.org/ontology/')
skos = Namespace ('http://www.w3.org/2004/02/skos/core#') 
xsd = Namespace ('http://www.w3.org/2001/XMLSchema#') 

# These are the URIs of the RDF vocabularies that we can load
vocabs = {
    'dates': 'http://www.eagle-network.eu/voc/dates.rdf', 
    'nomisma': 'http://nomisma.org/ontology.rdf'
}

# Load the Nomisma vocabularies so we can query them locally
g_dates = Graph()
g_dates.parse(vocabs['dates'], format="xml")
g_nomisma = Graph()
g_nomisma.parse(vocabs['nomisma'], format="xml")

def lookup_nomisma(label, gr, material, object_type, mint, date, end_date, legend, iconography, findspot, issue, ethnic):
	"""Tries to find a string match for a given label in a selected
	Nomisma controlled vocabulary."""
	# First check if a cached result exists
	map = globals()['map_' + gr]
	if label in map: return map[label]
	if label in map['_miss_']: return None
	# If not, do a local SPARQL query on the Nomisma vocabulary 
	graph = globals()['g_' + gr]
	q = """PREFIX nmo: <http://nomisma.org/ontology#>
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

def find_matches_researchspace( mappings ):
	"""Does a bulk lookup of the supplied mappings to ResearchSpace IDs 
	in order to generate owl:sameAs links."""
	from SPARQLWrapper import SPARQLWrapper, JSON, N3
	values = 'VALUES( ?x ?id ) {'
	for x, id in mappings.items():
		values += '( <' + str(x) + '> "' + str(id) + '" )'
	values += '}'
	sparql = SPARQLWrapper("https://collection.britishmuseum.org/sparql") 
	query = ("""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
CONSTRUCT { ?x <http://www.w3.org/2002/07/owl#sameAs> ?same } 
WHERE { """ 
+ values + """
  ?same crm:P48_has_preferred_identifier [
  	  crm:P2_has_type <http://collection.britishmuseum.org/id/thesauri/identifier/prn>
  	; <http://www.w3.org/2000/01/rdf-schema#label> ?id
  ]
}
	""")
	print(query)
	sparql.setQuery(query)
	sparql.setReturnFormat(N3)
	results = sparql.query().convert()
	return Graph().parse(data=results,format="n3")

uricache = {}
def make_uuid(item, graph, index = -1):
	# All the URIs we create for Nomisma coins will start like this
	base_uri = "http://data.open.ac.uk/baetica/coin/"
	uuid = None
	if 'ID' in item and item['ID'] and 'Series ' in item and item['Series '] :
		locn = item['ID'].strip()
		series = item['Series '].strip()
		if locn in uricache and series in uricache[locn] : 
			print('[WARN] there is already an item for {0} series {1} : {2}'.format(locn, series, uricache[locn][series]))
		else:
			p = re.compile('\s*\(.+\)')
			hasz = abs(hash(locn + '/' + series)) % (10 ** 8)
			locn_sane = p.sub('', locn.lower().replace('/','--')).strip().replace(' ','_')
			uuid = base_uri + locn_sane + '/' + str(hasz)
			if not locn in uricache : uricache[locn] = {}
			uricache[locn][series] = uuid
	else: print('[WARN] Could not find suitable UUID to make an URI from.')
	return uuid

g = Graph() # The final RDF graph

# Get the Nomisma data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
print('Slicing Google sheet NomismaMintsNew to range A:AZ ...')
list = google.get_data('NomismaMintsNew', 'A:AZ')
print('Done. Got {:d} elements'.format(len(list)))


mappings_rs = {}
for i, item in enumerate(list):
	subj = make_uuid(item, g, i)
	if subj :
		subj = URIRef(subj)
		
		# Add some types (for rdf:type and other taxonomical properties)
		g.add( ( subj, rdf.type, crm.E22 ) )
		g.add( ( subj, nmo.hasObjectType, nmo.Coin ) )
		g.add( ( subj, rs.PX_object_type, URIRef('http://collection.britishmuseum.org/id/thesauri/x6089') ) )
		
		# Make labels
		if 'ID' in item and item['ID'] and 'Series ' in item and item['Series '] :
			locn = item['ID'].strip()
			series = item['Series '].strip()
			g.add( ( subj, rdfs.label, Literal(locn + ' series ' +series, lang='en') ) )
		
		# Deal with mints. Note: the URIs ending with #this are NOT mints!
		if 'Mint' in item and item['Mint'] :
			mint = item['Mint'].strip()
			p = rs.Thing_created_at_Place if mint.endswith('#this') else nmo.hasMint
			g.add( ( subj, URIRef(p), URIRef(mint) ) )
			
		# Create the "location" predicate when there is a Pleiades URI
		if 'Pleiades URI' in item and item['Pleiades URI']:
			g.add( ( subj, geo.location, URIRef(item['Pleiades URI']) ) )
			
		# Check for British Museum ResearchSpace mappings and save them for later
		if 'BM' in item and item['BM']:
			mappings_rs[subj] = item['BM'].strip()

		# Look for an exact match on the material (using the Eagle vocabulary)
		if 'Material ' in item and item['Material ']:
			match = lookup_eagle(item['Material '], 'material', 'https://www.eagle-network.eu/voc/material/')
			if match: g.add( ( subj, crm.P45, URIRef(match) ) )
			
		# Look for an exact match on the object type (using the Eagle vocabulary)
		if 'Type' in item and item['Type']:
			match = lookup_eagle(item['Type'], 'object_type', 'https://www.eagle-network.eu/voc/objtyp/')
			if match: g.add( ( subj, crm.P2, URIRef(match) ) )

for t in find_matches_researchspace( mappings_rs ):
	g.add(t)

# Print the graph in Turtle format
g.namespace_manager.bind('bm', URIRef('http://collection.britishmuseum.org/id/thesauri/'))
g.namespace_manager.bind('crm', URIRef('http://www.cidoc-crm.org/cidoc-crm/'))
g.namespace_manager.bind('nmo', URIRef('http://nomisma.org/ontology#'))
g.namespace_manager.bind('owl', URIRef('http://www.w3.org/2002/07/owl#'))
g.namespace_manager.bind('rs', URIRef('http://www.researchspace.org/ontology/'))

# ... to a file 'out/nomisma.ttl' (will create the 'out' directory if missing)
dir = 'out'
if not os.path.exists(dir):
    os.makedirs(dir)
# Note: it will overwrite the existing Turtle file!
path = os.path.join(dir, 'nomisma.ttl')
g.serialize(destination=path, format='turtle')
print('DONE. Output graph written to ' + path)
# Uncomment the following to print to screen instead of file
# print(g.serialize(format='turtle').decode('utf8'))
    
    
   
    

