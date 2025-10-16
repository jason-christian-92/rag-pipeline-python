import argparse
import os
import json
from dotenv import load_dotenv

from classes.supabase_conn import SupabaseConnection
from classes.file_io import FileIO
from classes.rag_pipeline import RAGPipeline

# Load from .env variable
load_dotenv()

# parse arguments from terminal
parser = argparse.ArgumentParser("rag-manager")
parser.add_argument("--action", help="chosen action")
parser.add_argument("--foldername", help="the foldername containing the files to be embedded")
parser.add_argument("--query", help="user query for AI search")
args = parser.parse_args()

# grab the args
action = args.action
foldername = args.foldername
query = args.query

# Database to store the embeddings
sbConn = SupabaseConnection(os.getenv("SUPABASE_API_URL"), os.getenv("SUPABASE_API_KEY"))

# Whole pipeline for querying and storing
rag_pipeline = RAGPipeline(os.getenv("SENTENCE_TRANSFORMER_MODEL"), os.getenv("LLM_MODEL"), sbConn)

# ------------------------BEGIN PROCESS
if action == "store":
	# Extract doc and store it
	if foldername is None or foldername == "":
		print ("Missing --foldername parameter")
	else:
		rag_pipeline.store_files_as_embeddings(foldername, True)
elif action == "query":
	# Query relevant documents
	if query is None or query == "":
		print("--query cannot be empty")
	else:
		print("Querying relevant documents for '" + query + "'...")
		result = rag_pipeline.query_documents(query)
		print("Documents ranked by relevancy to the query:")
		for item in result:
			print ("-", 
				item['doc_name'], 
				"Page: "+str(item['page']), 
				"Similarity: "+str(item['similarity'])
			)
elif action == "ask":
	# ask stuff
	if query is None or query == "":
		print ("--query cannot be empty")
	else:
		print ("AI is looking for answer...")
		answer = rag_pipeline.query_answer(query)
		print ("=======")
		print (answer)
else:
	# Unknown action
	print("Unknown action " + action)
# ------------------------END PROCESS