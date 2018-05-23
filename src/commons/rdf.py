#!/usr/bin/env python

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
import unidecode

crm = Namespace('http://erlangen-crm.org/current/')

def make_basic_entity(label, graph, type):
	"""Creates the generic triples for an entity ex novo"""
	if not label : return None
	base_uri = 'http://data.open.ac.uk/baetica/'
	lsani = unidecode.unidecode(label.strip().lower().replace(' ','_'))
	if   type ==       crm.E55_Type : t = 'objtyp'
	elif type ==   crm.E57_Material : t = 'material'
	elif type == crm.E78_Collection : t = 'collection'
	else: t = 'thing'
	subj = URIRef(base_uri + t + '/' + lsani)
	graph.add( ( subj, RDF.type, URIRef(type) ) )
	graph.add( ( subj, RDFS.label, Literal(label,lang='en') ) )
	return subj