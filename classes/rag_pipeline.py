import mimetypes
import os
from sentence_transformers import SentenceTransformer
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from .file_io import FileIO

class RAGPipeline:
	
	embeddingsExtModel = None
	supabaseDbConn = None
	llmModel = None

	# Initialize the LLM model, vector DB connection, and embeddings model
	def __init__(self, extractionModel, llmModel, supabaseConnection):
		self.embeddingsExtModel = SentenceTransformer(extractionModel);
		self.supabaseDbConn = supabaseConnection
		self.llmModel = OllamaLLM(model=llmModel)

	# Convert the content of a file into embeddings
	def store_files_as_embeddings(self, dirPath, verbose=False):
		for file in os.listdir(dirPath):
			fPath = os.path.join(dirPath, file)
			print ("Extracting embedding from "+fPath+"...") if verbose else None
			content = self.embeddings_from_file(fPath) 
			print ("storing embeddings...") if verbose else None
			self.store_embeddings(os.getenv("SUPABASE_TABLE_NAME"), fPath, content)

	# Query documents relevant to the given query string
	def query_documents(self, queryString):
		queryVector = self.encode_text_to_embedding(queryString)
		response = self.supabaseDbConn.rpc("query_documents", {
			"query_embedding": queryVector.tolist()
		})
		return response.data

	# Return answer from AI with the given query string
	def query_answer(self, queryString):
		response = self.query_documents(queryString)
		if (len(response) == 0):
			# No relevant documents found. Tell the LLM to show generic "don't know"
			promptTemplate = ChatPromptTemplate.from_template(FileIO.text_from_file("prompts/prompt_noidea.txt"))
			prompt = promptTemplate.format(question = queryString)
		else:
			# Grab 2 of the most relevant documents
			# TODO find out how to limit the source (num of docs, similarity, etc. etc.)
			relevantDocs = response[:2]
			relevantDocsContent = [FileIO.read_pdf(x['doc_name'], x['page']-1) for x in relevantDocs]
			# generate prompt
			promptTemplate = ChatPromptTemplate.from_template(FileIO.text_from_file("prompts/prompt_template.txt"))
			prompt = promptTemplate.format(context = "\n\n".join(relevantDocsContent), question = queryString)

		# ask the LLM
		answer = self.llmModel.invoke(prompt)
		return answer

	# Convert the given string into embeddings
	def encode_text_to_embedding(self, text):
		return self.embeddingsExtModel.encode(text)

	# Convert the content of the file into array of embeddings
	def embeddings_from_file(self, fPath):
		fSpec = mimetypes.guess_type(fPath)
		if (fSpec[0] == "application/pdf"):
			chunks = FileIO.read_whole_pdf(fPath)
			embeddings = [self.encode_text_to_embedding(x) for x in chunks]
			# Will return embedding per page from PDF
			return embeddings

		# TODO other file ext
		
		return None

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