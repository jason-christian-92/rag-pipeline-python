import requests
from bs4 import BeautifulSoup

class WebCrawler:

	__htmlTags = [
		"div", "p"
	]

	def get_text(self, url):
		htmltext = requests.get(url).text
		soup = BeautifulSoup(htmltext, "html.parser")

		# try removing footer and header
		footer = soup.find_all(["footer", "header"])
		for f in footer:
			f.decompose()

		# find all possible text content
		tags = soup.find_all(self.__htmlTags)
		textChunks = []
		for t in tags:
			# strip empty space, tab and new lines
			innertext = t.text.strip().replace("\n", " ").replace("\t", " ")
			
			# Don't store short text. We focus on longer ones
			# Avoid possible duplicate text as well
			if(innertext is not None 
				and len(innertext) > 200 
				and innertext not in textChunks):
				
				textChunks.append(innertext)

		return textChunks