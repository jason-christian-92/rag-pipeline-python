from supabase import create_client, Client
from dotenv import load_dotenv

class SupabaseConnection:
	
	connObject = None

	def __init__(self, apiUrl, apiKey):
		self.connObject = create_client(apiUrl, apiKey)

	def rpc(self, functionName, functionParam):
		return self.connObject.rpc(functionName, functionParam).execute()

	def insert(self, tblName, param):
		try:
			self.connObject.table(tblName).insert(param).execute()
		except Exception as e:
			print("Failed to store:", e)