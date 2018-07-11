#pip install SPARQLWrapper
#python

from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("https://collection.britishmuseum.org/sparql") 
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core>
    PREFIX thes: <http://collection.britishmuseum.org/id/thesauri/>
    PREFIX rso: <http://www.researchspace.org/ontology/>
     SELECT DISTINCT ?coin WHERE {
  ?coin rso:PX_object_type/skos:broader* thes:x6089
  ; rso:Thing_from_Place/(<http://www.cidoc-crm.org/cidoc-crm/P88i_forms_part_of>|^rso:Place_has_part_Place|skos:broader)* <http://collection.britishmuseum.org/id/place/x22782>
  }  LIMIT 10
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results ["results"]["bindings"]:
    print (result["coin"]["value"])
