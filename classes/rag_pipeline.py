import mimetypes
import os
from sentence_transformers import SentenceTransformer
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from .file_io import FileIO
from .web_crawler import WebCrawler

class RAGPipeline:
	
	embeddingsExtModel = None
	supabaseDbConn = None
	llmModel = None
	fileIO = FileIO()
	webCrawler = WebCrawler()
	__tableName = None

	# Initialize the LLM model, vector DB connection, and embeddings model
	def __init__(self, extractionModel, llmModel, supabaseConnection):
		self.embeddingsExtModel = SentenceTransformer(extractionModel);
		self.supabaseDbConn = supabaseConnection
		self.llmModel = OllamaLLM(model=llmModel)
		self.__tableName = os.getenv("SUPABASE_TABLE_NAME")

	# Convert the content of a file into embeddings
	def store_files_as_embeddings(self, dirPath, verbose=False):
		for file in os.listdir(dirPath):
			fPath = os.path.join(dirPath, file)
			print ("Extracting embedding from "+fPath+"...") if verbose else None
			content = self.embeddings_from_file(fPath) 
			print ("storing embeddings...") if verbose else None
			self.store_embeddings(self.__tableName, fPath, content)

	# Query documents relevant to the given query string
	def query_documents(self, queryString):
		queryVector = self.encode_text_to_embedding(queryString)
		response = self.supabaseDbConn.rpc("query_documents", {
			"query_embedding": queryVector.tolist()
		})
		return response.data

	# Return answer from AI with the given query string
	def query_answer(self, queryString, verbose=False):
		response = self.query_documents(queryString)
		if (len(response) == 0):
			# No relevant documents found. Tell the LLM to show generic "don't know"
			promptTemplate = ChatPromptTemplate.from_template(self.fileIO.text_from_file("prompts/prompt_noidea.txt"))
			prompt = promptTemplate.format(question = queryString)
		else:
			# Grab 2 of the most relevant documents
			# TODO find out how to limit the source (num of docs, similarity, etc. etc.)
			relevantDocs = response[:2]

			if verbose:
				print("Docs most relevant to the query:")
				for rd in relevantDocs:
					print("-", 
						rd["doc_name"],
						" at page " + str(rd["page"]),
						" with similarity score " + str(rd["similarity"])
					)

			relevantDocsContent = [self.fileIO.read_pdf(x['doc_name'], x['page']-1) for x in relevantDocs]
			# generate prompt
			promptTemplate = ChatPromptTemplate.from_template(self.fileIO.text_from_file("prompts/prompt_template.txt"))
			prompt = promptTemplate.format(context = "\n\n".join(relevantDocsContent), question = queryString)

		# ask the LLM
		answer = self.llmModel.invoke(prompt)
		return answer

	def crawl_and_store_info(self, url, verbose=False):
		textChunks = self.webCrawler.get_text(url)
		wholeText = ("\n\n").join(textChunks)
		embedding = [self.encode_text_to_embedding(wholeText)]
		self.store_embeddings(self.__tableName, url, embedding)

	# Convert the given string into embeddings
	def encode_text_to_embedding(self, text):
		return self.embeddingsExtModel.encode(text)

	# Convert the content of the file into array of embeddings
	def embeddings_from_file(self, fPath):
		fSpec = mimetypes.guess_type(fPath)
		chunks = []
		if (fSpec[0] == "application/pdf"):
			chunks = self.fileIO.read_whole_pdf(fPath)
			embeddings = [self.encode_text_to_embedding(x) for x in chunks]
			# Will return embedding per page from PDF
			return embeddings
		elif fSpec[0] == "text/plain":
			chunks = [self.fileIO.text_from_file(fPath)]
		else:
			print(f"Unsupported type: {fSpec[0]}")

		# TODO other file ext
		
		embeddings = [self.encode_text_to_embedding(x) for x in chunks]
		return embeddings

	# Store the embeddings in the database
	def store_embeddings(self, tableName, docName, embeddings):
		page = 1
		for embd in embeddings:
			param = { 
				"doc_name": docName, 
				"embedding": embd.tolist(), 
				"page": page 
			}
			self.supabaseDbConn.insert(tableName, param)
			page += 1