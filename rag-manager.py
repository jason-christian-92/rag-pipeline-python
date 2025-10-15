import argparse
import os
import json
import mimetypes
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from pypdf import PdfReader

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

# Model for creating embeddings
extractionModel = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMER_MODEL"));
# Database to store the embeddings (TODO put in env)
supabaseConn = create_client(
	os.getenv("SUPABASE_API_URL"), 
	os.getenv("SUPABASE_API_KEY")
)
supabaseTableInfo = {
	"tblName": os.getenv("SUPABASE_TABLE_NAME"),
	"colDocName": os.getenv("SUPABASE_COL_DOC"),
	"colEmbd": os.getenv("SUPABASE_COL_EMBEDDING"),
	"colPage": os.getenv("SUPABASE_COL_PAGE")
}

def encode_text_to_embedding(text, model):
	return model.encode(text)

# BEGIN DEF: Extract embeddings from content of file
def extract_embeddings(fPath, model = None):
	if model is None:
		model = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMER_MODEL"));
	
	fSpec = mimetypes.guess_type(fPath)
	if (fSpec[0] == "application/pdf"):
		reader = PdfReader(fPath)
		embeddings = []
		for i in range(0, len(reader.pages)):
			chunk = reader.pages[i].extract_text()
			embedding = encode_text_to_embedding(chunk, model)
			embeddings.append(embedding)

		# Will return embedding per page in PDF
		return embeddings
	return None
# END DEF: Extract embeddings

# BEGIN DEF: Store embeddings to SupaBase database
def store_embeddings(docName, embeddings, conn):
	page = 1
	for embd in embeddings:
		param = { 
			supabaseTableInfo['colDocName']: docName, 
			supabaseTableInfo['colEmbd']: embd.tolist(), 
			supabaseTableInfo['colPage']: page 
		}
		conn = conn.table(supabaseTableInfo['tblName']).insert(param)
	try:
		conn.execute()
	except Exception as e:
		print("Failed to store:", e)
# END DEF: Store embeddings to SupaBase database

# BEGIN DEF: query the database and retrieve the documents relevant to it
def query_database(queryString):
	queryVector = encode_text_to_embedding(queryString, extractionModel)
	response = supabaseConn.rpc("query_documents", {
		"query_embedding": queryVector.tolist()
	}).execute()
	return response
# END DEF

# BEGIN PROCESS
if action == "store":
	# Extract doc and store it
	if foldername is None or foldername == "":
		print ("Missing --foldername parameter")
	else:
		for file in os.listdir("docs"):
			fPath = os.path.join(foldername, file)
			print ("Extracting embedding from "+fPath+"...")
			content = extract_embeddings(fPath, extractionModel)
			print ("storing embeddings...")
			store_embeddings(fPath, content, supabaseConn)
elif action == "query":
	# Query stuff
	if query is None or query == "":
		print("--query cannot be empty")
	else:
		print("Querying '" + query + "'...")
		result = query_database(query)
		print("Documents ranked by relevancy to the query:")
		for item in result.data:
			print ("-", item['doc_name'], item['page'], item['similarity'])
else:
	# Unknown action
	print("Unknown action " + action)
# END PROCESS