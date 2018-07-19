import rdflib
from rdflib import Graph
import re
import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen

def fix_turtle(ttl):
	"""Attemps to make the DARE Turtle code readable for RDFlib."""
	# The FOAF prefix bindings seems to be missing sometimes:
	# it won't hurt if it is added twice.
	ttl = "@prefix foaf: <http://xmlns.com/foaf/0.1/> . " + ttl
	return ttl

with open('dare-test.txt') as baetica:
    b = []
    for l in baetica:
        if re.match('http://',l):
            pl = l.rstrip()+'.ttl'
            
            with urlopen(pl) as url:
                http_info = url.info()
#                data = url.read().decode(http_info.get_content_charset())
                data = url.read().decode('utf8')
                data = fix_turtle(data)
                dare_places_in_baetica = Graph()
                dare_places_in_baetica.parse(data=data, format=rdflib.util.guess_format(pl))
                # Note that print() on a Graph does not achieve the expected result.
                print (dare_places_in_baetica)
                # Try to iterate over it instead.

""" 				               
from rdflib import Graph
import re
import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen
import pprint


with open('dare-test.txt') as baetica:
    b = []
    for l in baetica:
        if re.match('http://',l):
            pl = l.rstrip()+'.ttl'
            print(pl)
            g = Graph()
            bae = g.parse(pl)
            print(bae)
            
            
            with urlopen(pl) as url:
                http_info = url.info()
                print(http_info)
                data = url.read().decode(http_info.get_content_charset())
                ttl = url.read().decode('utf8')
                g = Graph()
                g.parse(data=url.read().decode('utf8'),format="n3")
                print(len(g))
"""