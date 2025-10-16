from pypdf import PdfReader

class FileIO:

	def read_whole_pdf(path):
		reader = PdfReader(path)
		return [p.extract_text() for p in reader.pages]

	def read_pdf(path, pageNum = 0):
		reader = PdfReader(path)
		pageFile = reader.pages[pageNum]
		return pageFile.extract_text()

	def text_from_file(path):
		f = open(path)
		content = f.read()
		f.close()
		return content