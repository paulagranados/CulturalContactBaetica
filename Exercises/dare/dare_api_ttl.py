import rdflib
from rdflib import Graph
import re
import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen


with open('dare-test.txt') as baetica:
    b = []
    for l in baetica:
        if re.match('http://',l):
            pl = l.rstrip()+'.ttl'
            
            with urlopen(pl) as url:
                http_info = url.info()
#                data = url.read().decode(http_info.get_content_charset())
                data = url.read().decode('utf8')
                dare_places_in_baetica = Graph()
                dare_places_in_baetica.parse(data=data,format=rdflib.util.guess_format(pl))
 				print (data) 
 				               
#from rdflib import Graph
#import re
#import urllib.request, urllib.parse, urllib.error
#from urllib.request import urlopen
#import pprint


#with open('dare-test.txt') as baetica:
 #   b = []
  #  for l in baetica:
   #     if re.match('http://',l):
    #        pl = l.rstrip()+'.ttl'
     #       print(pl)
      #      g = Graph()
       #     bae = g.parse(pl)
        #    print(bae)
            
            
#            with urlopen(pl) as url:
#                http_info = url.info()
#                print(http_info)
#                data = url.read().decode(http_info.get_content_charset())
#                ttl = url.read().decode('utf8')
#                g = Graph()
#                g.parse(data=url.read().decode('utf8'),format="n3")
#                print(len(g))