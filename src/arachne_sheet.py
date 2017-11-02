# coding: utf-8

import csv
import rdflib

from rdflib import Graph, Namespace, URIRef

crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

g = Graph()
list = []

with open('../data/ext/arachne/main.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)[1:]
    for row in reader:
    	dict = {key: value for key, value in zip(headers, row[1:])}
    	list.append(dict)

base_uri = "http://data.open.ac.uk/baetica/physical_object/ext-arachne/"

for item in list:
	subj = ''
	if item['URI']:
		id = item['URI'].rsplit('/', 1)[-1]
		if id.isdigit():
			subj = base_uri + id
			g.add( ( URIRef(subj), rdf.type, crm.E24 ) )
	if subj and item['Pleiades URI']:
		g.add( ( URIRef(subj), geo.location, URIRef(item['Pleiades URI']) ) )
			
print(g.serialize(format='n3').decode('utf8'))
