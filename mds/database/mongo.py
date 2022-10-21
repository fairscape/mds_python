from pymongo import MongoClient
from mds.database.config import MONGO_CONNECTION_STRING



class MongoConfig:
    def __init__(self, host_uri: str, port: int, user: str, password: str, database: str = None):
        self.host_uri = host_uri
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def connect(self) -> MongoClient:
        return MongoClient(MONGO_CONNECTION_STRING)


def GetConfig():
    return MongoClient(MONGO_CONNECTION_STRING)
    #return MongoConfig(
    #    host_uri= MONGO_URI,
    #    port=27017,
    #    user=MONGO_USER,
    #    password=MONGO_PASS,
    #    database=MONGO_DATABASE
    #).connect()
