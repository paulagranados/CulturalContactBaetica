<<<<<<< HEAD
#pip install SPARQLWrapper
#python

from SPARQLWrapper import Wrapper, RDF, TURTLE
=======
pip install SPARQLWrapper
python
import rdflib
From rdflib import Namespace, Graph, URIRef
from SPARQLWrapper import SPARQLWrapper
>>>>>>> 000c3937e5007f17bd4a11da7ecdf4a568734724
sparql = SPARQLWrapper("https://collection.britishmuseum.org/sparql") 
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX thes: <http://collection.britishmuseum.org/id/thesauri/>
    PREFIX rso: <http://www.researchspace.org/ontology/>PREFI
<<<<<<< HEAD
     CONSTRUCT DISTINCT ?y WHERE {
=======
     SELECT DISTINCT ?y WHERE {
>>>>>>> 000c3937e5007f17bd4a11da7ecdf4a568734724
  ?y rso:PX_object_type/skos:broader* thes:x6089
  ; rso:Thing_from_Place/(<http://www.cidoc-crm.org/cidoc-crm/P88i_forms_part_of>|^rso:Place_has_part_Place|skos:broader)* <http://collection.britishmuseum.org/id/place/x22782>
}
""")
sparql.setReturnFormat(TURTLE)
results = sparql.query().convert()
for result in results:   
    print(results.serialize)
    