import pymongo
from urllib.parse import quote_plus

class MongoConfig():
	def __init__(self, host_uri: str, port: int, user: str, password: str, database: str):
		self.host_uri = host_uri
		self.port = port 
		self.user = user
		self.password = password
		self.database = database


	def connect(self) -> pymongo.MongoClient: 
		connection_uri = f"mongodb://{quote_plus(self.user)}:" + f"{quote_plus(self.password)}@{self.host}:{str(self.port)}"
		return pymongo.MongoClient(connection_uri)