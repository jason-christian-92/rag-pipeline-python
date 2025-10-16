import pymupdf

class FileIO:

	def read_whole_pdf(self, path):
		doc = pymupdf.open(path)
		allChunks = []
		for page in doc:
			pageChunk = self.__do_extract_pdf_page_chunks(page)
			allText = pageChunk["text"] + "\n\n" + pageChunk["table"]
			# Add to chunks
			allChunks.append(allText)
			
		return allChunks

	def read_pdf(self, path, pageNum = 0):
		doc = pymupdf.open(path)
		pageFile = doc[pageNum]
		pageChunk = self.__do_extract_pdf_page_chunks(pageFile)
		return pageChunk["text"] + "\n\n" + pageChunk["table"]

	def text_from_file(self, path):
		f = open(path)
		content = f.read()
		f.close()
		return content

	def __do_extract_pdf_page_chunks(self, pdfPage):
		pageChunks = {}
			
		# extract the text
		pageChunks["text"] = pdfPage.get_text()

		# extract table content
		tables = pdfPage.find_tables()
		tableText = ""
		for table in tables:
			# Extract header
			header = ("||").join(
				[ name if name is not None else "" for name in table.header.names ]
			)
			tableText += header + "\n"

			# Extract the rows
			for row in table.extract():
				row_text = ("||").join(
					[ cell if cell is not None else "" for cell in row ]
				)
				tableText += row_text + "\n"

			tableText += "\n"

		pageChunks["table"] = tableText

		# TODO extract images

		return pageChunks