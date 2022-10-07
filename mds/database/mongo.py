from pymongo import MongoClient
from urllib.parse import quote_plus
from mds.database.config import MONGO_URI, MONGO_USER, MONGO_PASS, MONGO_DATABASE, MONGO_PORT
from os import environ


MONGO_CONNECTION_STRING = environ.get("MONGO_CONNECTION_STRING")

if MONGO_CONNECTION_STRING is None:
    
    if environ.get("MONGO_USER") is None:
        MONGO_CONNECTION_STRING = "mongodb://root:example@localhost:27017"
    else:
        MONGO_CONNECTION_STRING = f"mongodb://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASS)}@{MONGO_URI}:{str(MONGO_PORT)}/{MONGO_DATABASE}"


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
