#go to periodo
#get the periodo data in JSON
#keep the data into a file in the folder
#take the values from the google spreadsheet. 
#Then take the time period and use the value to make a string match with Periodo. 
#Make a parameter with the string you take for the time period. 
#generate the RDF triple that notices this alignment

import google

from rdflib import Graph, plugin
from rdflib.serializer import Serializer

pj = open('periodo_periods.json')
perjson = pj.read()

g = Graph().parse(data=perjson, format='json-ld')
def lookup_per (time_period):
    q = """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?x
WHERE {
   ?x skos:inScheme <""" + type + """>
    ; skos:altLabel ?l FILTER( lcase(str(?l)) = '""" + label.lower() + """' )
}"""