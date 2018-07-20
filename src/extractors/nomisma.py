# coding: utf-8

import os, re
from json import JSONDecodeError
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, OWL, RDF, RDFS, XSD
import unidecode
from urllib.parse import urlparse, parse_qs
from urllib.error import URLError

import google # Local module

print('Running Nomisma (new data) extractor (from Google sheet)...\n')

# Define Utility RDF prefixes
crm = Namespace('http://erlangen-crm.org/current/')
dct = Namespace ('http://purl.org/dc/terms/') 
geo = Namespace ('http://www.w3.org/2003/01/geo/wgs84_pos#') 
osgeo = Namespace ('http://data.ordnancesurvey.co.uk/ontology/geometry/') 
nmo = Namespace ('http://nomisma.org/ontology#') 
nm = Namespace ('http://nomisma.org/id/')
rdf = Namespace ('http://www.w3.org/1999/02/22-rdf-syntax-ns#') # for containers
rs = Namespace ('http://www.researchspace.org/ontology/')
skos = Namespace ('http://www.w3.org/2004/02/skos/core#')
spatial = Namespace ('http://geovocab.org/spatial#')

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
	in order to generate links using hasInstance."""
	from SPARQLWrapper import SPARQLWrapper, JSON, N3
	values = 'VALUES( ?x ?id ) {'
	for x, id in mappings.items():
		values += '( <' + str(x) + '> "' + str(id) + '" )'
	values += '}'
	#sparql = SPARQLWrapper("http://public.researchspace.org/sparql")
	sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql") 
	query = ("""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
CONSTRUCT { ?x <http://data.open.ac.uk/ontology/culturalcontact/hasInstance> ?same } 
WHERE { """ 
+ values + """
  ?same crm:P48_has_preferred_identifier [
  	  crm:P2_has_type <http://collection.britishmuseum.org/id/thesauri/identifier/prn>
  	; <http://www.w3.org/2000/01/rdf-schema#label> ?id
  ]
}
""")
	# print(query)
	sparql.setQuery(query)
	sparql.setReturnFormat(N3)
	try:
		results = sparql.query().convert()
	except:
		raise
	return Graph().parse(data=results,format="n3")

uricache = {}
def make_uuid(item, graph, index = -1):
	# All the URIs we create for Nomisma coins will start like this
	base_uri = "http://data.open.ac.uk/baetica/coin_type/"
	uuid = None
	if 'ID' in item and item['ID'] and 'Series ' in item and item['Series '] :
		locn = item['ID'].strip()
		series = item['Series '].strip()
		if locn in uricache and series in uricache[locn] : 
			print('[WARN] there is already an item for {0} series {1} : <{2}>'.format(locn, series, uricache[locn][series]))
		else:
			p = re.compile('\s*\(.+\)')
			hasz = abs(hash(locn + '/' + series)) % (10 ** 8)
			locn_sane = p.sub('', locn.lower().replace('/','--')).strip().replace(' ','_')
			uuid = base_uri + locn_sane + '/' + str(hasz)
			if not locn in uricache : uricache[locn] = {}
			uricache[locn][series] = uuid
	else: print('[WARN] row ' + str(index + 2) + ': Could not find suitable UUID to make an URI from.')
	return uuid

g = Graph() # The final RDF graph

# Get the Nomisma data from the online Google Sheet.
# To use the local CSV file instead, change google.get_data to localcsv.get_data
# and make sure the updated CSV file is in {project-dir}/data/ext/arachne/main.csv
print('Slicing Google sheet NomismaMintsNew to range A:BZ ...')
list = google.get_data('NomismaMintsNew', 'A:BZ')
print('Done. Got {:d} elements'.format(len(list)))

mappings_rs = {} # Keep track of ResearchSpace mappings
mappings_deity_auth = {} # A cache of DBpedia Spotlight searches for deities and authorities

# Now process the rows in the spreadsheet
for i, item in enumerate(list):
	subj = make_uuid(item, g, i)
	if subj :
		subj = URIRef(subj)
		label = ''
		
		# Add some types (for rdf:type and other taxonomical properties)
		g.add( ( subj, RDF.type, URIRef(nmo.TypeSeries) ) )
		# g.add( ( subj, RDF.type, OWL.Class ) )
		# g.add( ( subj, nmo.hasObjectType, nmo.Coin ) )
		g.add( ( subj, rs.PX_object_type, URIRef('http://collection.britishmuseum.org/id/thesauri/x6089') ) )
		
		# Make labels
		if 'ID' in item and item['ID'] and 'Series ' in item and item['Series '] :
			locn = item['ID'].strip()
			series = item['Series '].strip()
			label = locn + ' coin series ' + series
			g.add( ( subj, RDFS.label, Literal(label, lang='en') ) )

		# Deal with mints. Note: the URIs ending with #this are NOT mints!
		if 'Description' in item and item['Description'] :
			desc = item['Description'].strip()
			g.add( ( subj, RDFS.comment, Literal(desc, lang='en') ) )
		
		# Deal with mints. Note: the URIs ending with #this are NOT mints!
		if 'Mint' in item and item['Mint'] :
			mint = item['Mint'].strip()
			p = rs.Thing_created_at_Place if mint.endswith('#this') else nmo.hasMint
			g.add( ( subj, URIRef(p), URIRef(mint) ) )
			
		# Check for British Museum ResearchSpace mappings and save them for later
		if 'BM' in item and item['BM']:
			mappings_rs[subj] = item['BM'].strip()

		if 'Obv_Deity/Authority' in item and item['Obv_Deity/Authority']:
			dea = item['Obv_Deity/Authority'].strip()
			if dea not in mappings_deity_auth : mappings_deity_auth[dea] = []
			g.add( ( subj, URIRef('http://data.open.ac.uk/ontology/culturalcontact/temp/obverse_deityauth'), Literal(dea) ) )
			

		# Look for inscriptions, their languages etc.
		pref_rs_thes = 'http://collection.britishmuseum.org/id/thesauri/'
		# Obverse
		has_o_inscr = 'ObverseLegend1' in item and item['ObverseLegend1'] \
			or 'ObverseLanguage1' in item and item['ObverseLanguage1'] \
			or 'ObverseScript1' in item and item['ObverseScript1']
		has_o = 'ObverseDescription' in item and item['ObverseDescription']
		if has_o or has_o_inscr:
			obv = URIRef(subj + '/obverse')
			g.add( ( subj, crm.P65_shows_visual_item, obv ) ) # P65_shows_visual_item
			g.add( ( subj, nmo.hasObverse, obv ) )
			g.add( ( obv, RDF.type, crm.E36_Visual_Item ) ) # E36_Visual_Item
			if label: g.add( ( obv, RDFS.label, Literal('obverse of ' + label, lang='en') ) )
			if has_o : g.add( ( obv, dct.description, Literal(item['ObverseDescription'].strip(), lang='en') ) )
			if has_o_inscr :
				obvinscr = URIRef(subj + '/obverse/inscription')
				g.add( ( obv, crm.P128_carries, obvinscr ) ) # P128_carries
				g.add( ( obvinscr, RDF.type, crm.E34_Inscription ) ) # E34_Inscription
				g.add( ( obvinscr, RDF.type, RDF.Bag ) )
				obvinscr1 = URIRef(subj + '/obverse/inscription/1')
				g.add( ( obvinscr, rdf._1, obvinscr1 ) )
				g.add( ( obvinscr, RDFS.member, obvinscr1 ) )
				g.add( ( obvinscr1, RDF.type, crm.E34_Inscription ) ) # E34_Inscription
				if 'ObverseLegend1' in item and item['ObverseLegend1'] :
					g.add( ( obvinscr1, rs.PX_has_transliteration, Literal(item['ObverseLegend1'].strip(), datatype=XSD.string) ) )
				if 'ObverseLanguage1' in item and item['ObverseLanguage1'] :
					lang = item['ObverseLanguage1'].strip()
					ulang = URIRef(pref_rs_thes+'language/' + lang.lower().replace(' ','_'))
					g.add( ( obvinscr1, crm.P72_has_language, ulang ) )
					g.add( ( ulang, RDFS.label, Literal(lang, lang='en') ) )
				if 'ObverseScript1' in item and item['ObverseScript1'] :
					scr = item['ObverseScript1'].strip()
					uscr = URIRef(pref_rs_thes+'script/' + scr.lower().replace(' ','_'))
					g.add( ( obvinscr1, rs.PX_inscription_script, uscr ) )
					g.add( ( uscr, RDFS.label, Literal(scr, lang='en') ) )
					
		# Reverse
		has_r_inscr_1 = 'ReverseLegend1' in item and item['ReverseLegend1'] \
			or 'ReverseLanguage1' in item and item['ReverseLanguage1'] \
			or 'ReverseScript1' in item and item['ReverseScript1']
		has_r_inscr_2 = 'ReverseLegend2' in item and item['ReverseLegend2'] \
			or 'ReverseLanguage2' in item and item['ReverseLanguage2'] \
			or 'ReverseScript2' in item and item['ReverseScript2']
		has_r = 'ReverseDescription' in item and item['ReverseDescription']
		if has_r or has_r_inscr_1 or has_r_inscr_2:
			rev = URIRef(subj + '/reverse')
			g.add( ( subj, crm.P65_shows_visual_item, rev ) ) # P65_shows_visual_item
			g.add( ( subj, nmo.hasReverse, rev ) )
			g.add( ( rev, RDF.type, crm.E36_Visual_Item ) ) # E36_Visual_Item
			if label: g.add( ( rev, RDFS.label, Literal('reverse of ' + label, lang='en') ) )
			if has_r : g.add( ( rev, dct.description, Literal(item['ReverseDescription'].strip(), lang='en') ) )
			if has_r_inscr_1 or has_r_inscr_2:
				revinscr = URIRef(subj + '/reverse/inscription')
				g.add( ( rev, crm.P128_carries, revinscr ) ) # P128_carries
				g.add( ( revinscr, RDF.type, crm.E34_Inscription ) ) # E34_Inscription
				g.add( ( revinscr, RDF.type, RDF.Bag ) )
				if has_r_inscr_1 :
					revinscr1 = URIRef(subj + '/reverse/inscription/1')
					g.add( ( revinscr, rdf._1, revinscr1 ) )
					g.add( ( revinscr, RDFS.member, revinscr1 ) )
					g.add( ( revinscr1, RDF.type, crm.E34_Inscription ) ) # E34_Inscription
					if 'ReverseLegend1' in item and item['ReverseLegend1'] :
						g.add( ( revinscr1, rs.PX_has_transliteration, Literal(item['ReverseLegend1'].strip(), datatype=XSD.string) ) )
					if 'ReverseLanguage1' in item and item['ReverseLanguage1'] :
						lang = item['ReverseLanguage1'].strip()
						ulang = URIRef(pref_rs_thes+'language/' + lang.lower().replace(' ','_'))
						g.add( ( revinscr1, crm.P72_has_language, ulang ) )
						g.add( ( ulang, RDFS.label, Literal(lang, lang='en') ) )
					if 'ReverseScript1' in item and item['ReverseScript1'] :
						scr = item['ReverseScript1'].strip()
						uscr = URIRef(pref_rs_thes+'script/' + scr.lower().replace(' ','_'))
						g.add( ( revinscr1, rs.PX_inscription_script, uscr ) )
						g.add( ( uscr, RDFS.label, Literal(scr, lang='en') ) )
				if has_r_inscr_2 :
					revinscr2 = URIRef(subj + '/reverse/inscription/2')
					g.add( ( revinscr, rdf._2, revinscr2 ) )
					g.add( ( revinscr, RDFS.member, revinscr2 ) )
					g.add( ( revinscr2, RDF.type, crm.E34_Inscription ) ) # E34_Inscription
					if 'ReverseLegend2' in item and item['ReverseLegend2'] :
						g.add( ( revinscr2, rs.PX_has_transliteration, Literal(item['ReverseLegend2'].strip(), datatype=XSD.string) ) )
					if 'ReverseLanguage2' in item and item['ReverseLanguage2'] :
						lang = item['ReverseLanguage2'].strip()
						ulang = URIRef(pref_rs_thes+'language/' + lang.lower().replace(' ','_'))
						g.add( ( revinscr2, crm.P72_has_language, ulang ) )
						g.add( ( ulang, RDFS.label, Literal(lang, lang='en') ) )
					if 'ReverseScript2' in item and item['ReverseScript2'] :
						scr = item['ReverseScript2'].strip()
						uscr = URIRef(pref_rs_thes+'script/' + scr.lower().replace(' ','_'))
						g.add( ( revinscr2, rs.PX_inscription_script, uscr ) )
						g.add( ( uscr, RDFS.label, Literal(scr, lang='en') ) )

		# Look for an exact match on the material (using the Eagle vocabulary)
		if 'Material ' in item and item['Material ']:
			match = lookup_eagle(item['Material '], 'material', 'https://www.eagle-network.eu/voc/material/')
			if match: g.add( ( subj, crm.P45, URIRef(match) ) )

		# Correct to assume "Region" is the find spot?
		if 'Region' in item and item['Region']:
			base_uri = "http://data.open.ac.uk/baetica/"
			# Sanitise content
			split = re.split("[,/\?]", item['Region'])
			locs = []
			obj = None
			for sp in split:
				lloc = sp.strip()
				if lloc:
					loc = base_uri + 'place/' + unidecode.unidecode(lloc.lower().replace(' ','_'))
					locs.append(loc)
					g.add( ( URIRef(loc), RDF.type, crm.E53_Place ) )
					g.add( ( URIRef(loc), RDFS.label, Literal(lloc,lang='es') ) )
			locs.sort()
			if len(locs) > 1 :
				h = ''
				for i,loc in enumerate(locs):
					if i>0: h += ','
					h += loc
				hasz = abs(hash(h)) % (10 ** 8)
				obj = URIRef(base_uri + 'place/union/' + str(hasz))
				g.add( ( obj, RDF.type, crm.E53_Place ) )
				g.add( ( obj, RDFS.label, Literal(item['Region'].strip(),lang='es') ) )
				for loc in locs:
					g.add( ( obj, spatial.contains, URIRef(loc) ) )
			else : obj = locs[0]
			if obj: g.add( ( subj, nmo.hasFindspot, URIRef(obj) ) )
			
		# Look for an exact match on the object type (using the Eagle vocabulary)
		if 'Type' in item and item['Type']:
			match = lookup_eagle(item['Type'], 'object_type', 'https://www.eagle-network.eu/voc/objtyp/')
			if match: g.add( ( subj, crm.P2, URIRef(match) ) )

		# External non-semantic links
		if 'URI Item' in item and item['URI Item']:
			g.add( ( subj, RDFS.seeAlso, URIRef(item['URI Item'].strip()) ) )

# Now do all the external lookups
try:
	for t in find_matches_researchspace( mappings_rs ):
		g.add(t)
except URLError:
	print("[ERROR] ResearchSpace check failed. Not trying further.")
import search.dbpedia as spotlight
try:
	for txt in mappings_deity_auth:
		print('searching "' + txt + '" :')
		de = spotlight.annotations( txt, types=["DBpedia:Person","DBpedia:unknown"] )
		if 'Resources' in de :
			for res in de['Resources']:
				print('- '+res['@URI'])
				mappings_deity_auth[txt].append(res['@URI'])
except URLError:
	print("[ERROR] DBpedia Spotlight lookup failed. Not trying further.")
except JSONDecodeError as e:
	print("[ERROR] DBpedia Spotlight lookup returned unparsable content. Not trying further.")
	print(e)
for s,p,o in g.triples( (None, URIRef('http://data.open.ac.uk/ontology/culturalcontact/temp/obverse_deityauth'), None) ):
	odatxt = str(o)
	for s1,p1,obverse in g.triples( (s, nmo.hasObverse, None) ) :
		if odatxt in mappings_deity_auth and mappings_deity_auth[odatxt] :
			for oda in mappings_deity_auth[odatxt] :
				g.add( ( obverse, crm.P138_represents, URIRef(oda) ) )

g.remove( (None, URIRef('http://data.open.ac.uk/ontology/culturalcontact/temp/obverse_deityauth'), None) )
	

# Print the graph in Turtle format
g.namespace_manager.bind('bm', URIRef('http://collection.britishmuseum.org/id/thesauri/'))
g.namespace_manager.bind('cc', URIRef('http://data.open.ac.uk/ontology/culturalcontact/'))
g.namespace_manager.bind('crm', URIRef('http://erlangen-crm.org/current/'))
g.namespace_manager.bind('dct', URIRef('http://purl.org/dc/terms/'))
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
print('DONE. ' + str(len(g)) + ' triples written to ' + path)

# Uncomment the last line to print to screen instead of file
# ... but don't forget that the other messages printed earlier will get in the way!
# print(g.serialize(format='turtle').decode('utf8'))
    
    
   
    

