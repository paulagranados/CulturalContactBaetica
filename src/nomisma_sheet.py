import google

import rdflib
from rdflib import Graph, Namespace, URIRef
import re
from urllib.parse import urlparse, parse_qs

# Define Utility RDF prefixes
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
skos = Namespace ('http://www.w3.org/2004/02/skos/core#') 
prov = Namespace ('http://www.w3.org/ns/prov#') 
foaf = Namespace ('http://xmlns.com/foaf/0.1/') 
geo = Namespace ('http://www.w3.org/2003/01/geo/wgs84_pos#') 
osgeo = Namespace ('http://data.ordnancesurvey.co.uk/ontology/geometry/') 
nmo = Namespace ('http://nomisma.org/ontology#') 
dcterms= Namespace ('http://purl.org/dc/terms/') 
rdf = Namespace ('http://www.w3.org/1999/02/22-rdf-syntax-ns#') 
xsd = Namespace ('http://www.w3.org/2001/XMLSchema#') 
nm = Namespace ('http://nomisma.org/id/') 
org = Namespace ('http://www.w3.org/ns/org#') 
rdfs = Namespace ('http://www.w3.org/2000/01/rdf-schema#') 
un = Namespace ('http://www.owl-ontologies.com/Ontology1181490123.owl#') 

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

def lookup_researchspace(coins from Spain): 
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("https://collection.britishmuseum.org/sparql") 
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core>
    PREFIX thes: <http://collection.britishmuseum.org/id/thesauri/>
    PREFIX rso: <http://www.researchspace.org/ontology/>
     SELECT DISTINCT ?y WHERE {
  ?y rso:PX_object_type/skos:broader* thes:x6089
  ; rso:Thing_from_Place/(<http://www.cidoc-crm.org/cidoc-crm/P88i_forms_part_of>|^rso:Place_has_part_Place|skos:broader)* <http://collection.britishmuseum.org/id/place/x22782>
} LIMIT 10  
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results:   
    print(results.serialize)
    

def make_uuid(item, graph):
	base_uri = "http://data.open.ac.uk/baetica/coin/"
	uuid = None
	# prefer Nomisma over museums 
	if 'URI 1' in item and item['URI 1']:
		parsed = urlparse(item['URI 1'])		
		rexp = re.compile('/record/(\d+)/')
		matches = re.findall(rexp, parsed.path)
		if matches : uuid = base_uri + 'ext-/' + matches[0]
	if 'URI 2' in item and item['URI 2']:
		idd = item['ID']
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

# Get the Nomisma data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
list = google.get_data('NomismaMintsNew', 'A:L')

# All the URIs we create for sculptures etc. will start like this
base_uri = "http://data.open.ac.uk/baetica/coin/ext-nomisma/"

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
    
    
   
    

