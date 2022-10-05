from pymongo import MongoClient
from urllib.parse import quote_plus
from mds.database.config import MONGO_URI, MONGO_USER, MONGO_PASS, MONGO_DATABASE


class MongoConfig:
    def __init__(self, host_uri: str, port: int, user: str, password: str, database: str = None):
        self.host_uri = host_uri
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def connect(self) -> MongoClient:
        connection_uri = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host_uri}:{str(self.port)}/{self.database}"
        return MongoClient(connection_uri)


def GetConfig():
    return MongoConfig(
        host_uri= MONGO_URI,
        port=27017,
        user=MONGO_USER,
        password=MONGO_PASS,
        database=MONGO_DATABASE
    ).connect()
