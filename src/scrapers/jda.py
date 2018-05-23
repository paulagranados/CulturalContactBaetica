#!/usr/bin/env python

from bs4 import BeautifulSoup as Soup
import logging
from rdflib import Namespace
import requests
import unidecode

import commons.rdf as crdf # Local module

# Define Utility RDF prefixes
crm = Namespace('http://erlangen-crm.org/current/')

import commons.rdf as crdf

logger = logging.getLogger(__name__)

class JDA2RDF:

	def __init__(self, graph):
		self.graph = graph

	def build(self, data):
		"""
		inventario
		departamento
		clasif._generica
		objeto
		material/soporte
		tecnica/s
		dimensiones: Altura = x cmAnchura = y cmGrosor = z cmPeso = w gr
		descripcion
		iconografia
		contexto_cultural
		datacion
		uso/funcion
		procedencia
		clasif._razonada
		tipo_de_coleccion: Colección Estable
		"""
		# TODO include the museum short name for the collection URI
		if 'tipo_de_coleccion' in data and data['tipo_de_coleccion']:
			coll = crdf.make_basic_entity(data['tipo_de_coleccion'], self.graph, crm.E78_Collection)
		return self.graph
		
	def scrape(self,url):
		data = {}
		page = requests.get(url)
		if page.status_code != 200:
			print( '[WARN] Could not load page for scraping (HTTP Error {0}): {1}'.format(page.status_code, url) )
			return data
		soup = Soup(page.content, 'html.parser')
		for obra in soup.findAll(id='obras'):
			for field in obra.findAll('span', {'class' : 'colorMASE'}):
				k = unidecode.unidecode(field.get_text().strip().lower().replace(' ','_'))
				bro = field.find_next_sibling("p")
				if bro : v = bro.get_text()
				if k and v : data[k] = v.strip()
		return data