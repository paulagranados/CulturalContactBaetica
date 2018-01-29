import google 

import rdfLib
from rdfLib import Graph, Namespace, URIRef
import re
from urllib.parse import urlparse, parse_qs

#Define Utility RDF prefixes 
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
    'material': 'http://nomisma.org/ontology#Material' 
    'type': 'http://nomisma.org/ontology#ObjectType'
    'mint': 'http://nomisma.org/ontology#Mint'     
    'date': 'https://www.eagle-network.eu/voc/dates/">' 
    'endDate': 'http://nomisma.org/ontology#EndDate'  
    'legend': 'http://nomisma.org/ontology#Legend'
    'iconography': 'http://nomisma.org/ontology#Iconography'
    'findspot': 'http://nomisma.org/ontology#Findspot'
    'issuer': 'http://nomisma.org/ontology#Issuer' 
    'ethnic': 'http://nomisma.org/ontology#Ethnic'
    
}

# Load the Nomisma vocabularies so we can query them locally
g_material = Graph()
g_material.parse(vocabs['material'], format="xml")
g_object_type = Graph()
g_object_type.parse(vocabs['object_type'], format="xml")
g_mint = Graph ()
g_mint.parse(vocabs['mint'], format="xml")
g_date = Graph()
g_date.parse(vocabs['date'], format="xml")
g_end_date = Graph()
g_end_date.parse(vocabs['end_date'], format="xml")
g_legend = Graph()
g_legend.parse(vocabs['legend'], format="xml")
g_iconography = Graph()
g_iconography.parse(vocabs['iconography'], format="xml")
g_findspot = Graph()
g_fndspot.parse(vocabs['findspot'], format="xml")
g_issuer = Graph()
g_issuer.parse(vocabs['issuer'], format="xml")
g_ethnic = Graph()
g_ethnic.parse(vocabs['ethnic'], format="xml")

def lookup_nomisma(label, gr, type):
	"""Tries to find a string match for a given label in a selected
	Nomisma controlled vocabulary."""
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
    
    
   
    

