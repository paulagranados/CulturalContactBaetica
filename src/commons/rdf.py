#!/usr/bin/env python

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.namespace import FOAF
import unidecode

crm = Namespace('http://erlangen-crm.org/current/')

def make_basic_entity(label, graph, type):
	"""Creates the generic triples for an entity ex novo"""
	if not label : return None
	base_uri = 'http://data.open.ac.uk/baetica/'
	lsani = unidecode.unidecode(label.strip().lower().replace(' ','_'))
	if   type ==               None : t = 'thing'
	elif type ==       crm.E55_Type : t = 'objtyp'
	elif type ==   crm.E57_Material : t = 'material'
	elif type == crm.E78_Collection : t = 'collection'
	elif type ==         FOAF.Agent : t = 'agent'
	else : t = type.strip().lower().replace(' ','_')
	subj = URIRef(base_uri + t + '/' + lsani)
	graph.add( ( subj, RDF.type, URIRef(type) ) )
	graph.add( ( subj, RDFS.label, Literal(label,lang='en') ) )
	return subj