# coding: utf-8

import csv
import rdflib

from rdflib import Graph, Namespace, URIRef

# Define Utility RDF prefixes
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
ple_place = Namespace('https://pleiades.stoa.org/places/')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

g = Graph() # The final RDF graph
list = []   # Will contain the CSV content as an array of key:value pairs

# Open the CSV file (in another directory in the project) 
with open('../data/ext/arachne/main.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)[1:] # Parse the first line of the CSV and keep as headers
    for row in reader:
    	# Populate the array with objects of Dictionary type (i.e. associative 
    	# arrays with non-numerical keys 
    	dict = {key: value for key, value in zip(headers, row[1:])}
    	list.append(dict)

# All the URIs we create for sculptures etc. will start like this
base_uri = "http://data.open.ac.uk/baetica/physical_object/ext-arachne/"

for item in list:
	subj = ''
	if item['URI']:
		# Extract the Arachne ID from the URI and reuse it
		# TODO: not the best way to do it, we should get the JSON data for that
		# object and get the IR attribute of that
		id = item['URI'].rsplit('/', 1)[-1]
		if id.isdigit():
			subj = base_uri + id
			g.add( ( URIRef(subj), rdf.type, crm.E24 ) )
	# Create the "location" predicate when there is a Pleiades URI
	if subj and item['Pleiades URI']:
		g.add( ( URIRef(subj), geo.location, URIRef(item['Pleiades URI']) ) )
			
# Print the graph in Turtle format to screen
print(g.serialize(format='turtle').decode('utf8'))
