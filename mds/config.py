from enum import Enum
from pydantic import (
    BaseModel
)
from typing import (
    Optional
)
import os
import pathlib
from urllib.parse import quote_plus
from pymongo import MongoClient, ASCENDING
import minio
from functools import lru_cache

import casbin
import casbin_sqlalchemy_adapter
from dotenv import dotenv_values


#AUTH_ENABLED = bool(os.environ.get("MDS_AUTH_ENABLED", "True"))

@lru_cache()
def cached_dotenv():
    # TODO temporary hardcoded fix for path issues
    env_path = "./.env"
    config = {
        **dotenv_values(env_path),
        **os.environ,
    }
    return config

 
@lru_cache()
def get_mongo_config():

    config_values = cached_dotenv()

    return MongoConfig(
        host= config_values['MONGO_HOST'],
        port= config_values['MONGO_PORT'],
        user= config_values['MONGO_ACCESS_KEY'],
        password= config_values['MONGO_SECRET_KEY'],
        db= config_values['MONGO_DATABASE'],
        identifier_collection = config_values["MONGO_IDENTIFIER_COLLECTION"],
        user_collection = config_values["MONGO_USER_COLLECTION"],
        rocrate_collection = config_values["MONGO_ROCRATE_COLLECTION"]
    )


@lru_cache()
def get_mongo_client():
    mongo_config = get_mongo_config()
    return mongo_config.CreateClient()


@lru_cache()
def get_minio_config():

    config_values = cached_dotenv()

    return MinioConfig(
        host= config_values["MINIO_URI"],
        port=config_values["MINIO_PORT"],
        access_key = config_values["MINIO_ACCESS_KEY"],
        secret_key = config_values["MINIO_SECRET_KEY"],
        default_bucket= config_values["MINIO_DEFAULT_BUCKET"], 
        rocrate_bucket=config_values["MINIO_ROCRATE_BUCKET"],
        secure= bool(config_values["MINIO_SECURE"]=="True"),
    )


@lru_cache()
def get_minio_client():
   minio_config = get_minio_config()
   return minio_config.CreateClient()


@lru_cache()
def get_casbin_config():
    config_values = cached_dotenv()

    return CasbinConfig(
        policy_path= pathlib.Path(
            config_values["CASBIN_POLICY"]
        ),
        casbin_model_path= pathlib.Path(
            config_values["CASBIN_MODEL"]
        )
    )

@lru_cache()
def get_casbin_enforcer():
    casbin_config = get_casbin_config()
    return casbin_config.CreateClient()
 
@lru_cache()
def get_jwt_secret():
    config_values = cached_dotenv()
    return config_values["JWT_SECRET"]

@lru_cache()
def get_ark_naan():
    # TODO return entire config object
    config_values= cached_dotenv()
    return config_values.get("ARK_NAAN", "59853")

#MongoDep = Annotated[pymongo.MongoClient, Depends(common_parameters)]
#CasbinDep = Annotated[casbin.Enforcer, Depends(get_casbin)]
#MinioDep = Annotated[minio.MinioClient, Depends(get_minio)]


class MongoConfig(BaseModel):
    host: Optional[str] = "localhost"
    port: Optional[str] = "27017"
    user: Optional[str] = "user"
    password: Optional[str] = "pass"
    db: Optional[str] = "fairscape"
    identifier_collection: Optional[str] = "mds"
    rocrate_collection: Optional[str] = "rocrate"
    user_collection: Optional[str] = "users"
    session_collection: Optional[str] = "sessions"


    def CreateClient(self):

        #connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.db}"
        connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}"
        return MongoClient(connection_string)


class MinioConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None
    secret_key: Optional[str] = None
    access_key: Optional[str] = None
    default_bucket: Optional[str] = "mds"
    rocrate_bucket: Optional[str] = "rocrate"
    secure: bool


    def CreateClient(self):

        if self.port is None:
            uri = self.host
        else:
            uri = f"{self.host}:{self.port}"

        return minio.Minio(
                endpoint= uri, 
                access_key= self.access_key, 
                secret_key= self.secret_key,
                secure = self.secure
                )


class ComputeBackendEnum(str, Enum):
    docker = "docker"
    kubernetes = "kubernetes"


class RedisConfig(BaseModel):
    port: int
    uri: str
    broker_url: Optional[str]
    result_backend: Optional[str]


class K8sComputeConfig(BaseModel):
    redis: RedisConfig



class DockerConfig(BaseModel):
    pass
    

class CasbinAdapterEnum(str, Enum):
    """ Choices for supported Backends for Casbin Model Storage
    """
    sqlite = "sqlite"


class CasbinConfig(BaseModel):
    casbin_model_path: pathlib.Path
    policy_path: pathlib.Path 
    #backend: CasbinAdapterEnum

    def CreateClient(self):
        adapter = casbin_sqlalchemy_adapter.Adapter(f'sqlite:///{self.policy_path}')
        casbinEnforcer = casbin.Enforcer(str(self.casbin_model_path), adapter)
        return casbinEnforcer


class FairscapeConfig(BaseModel):
    host: str
    port: int
    reload_server: bool
    mongo: MongoConfig
    minio: MinioConfig
    compute: K8sComputeConfig
    casbin: CasbinConfig


    def CreateMongoClient(self):
        return self.mongo.CreateClient() 
    
    def CreateMinioClient(self):
        return self.minio.CreateClient()

    def StartWorker(self):
        celery_app = Celery('compute', include="mds.compute.tasks")
        app.conf.broker_url = self.compute.redis.broker_url
        app.conf.result_backend = self.compute.redis.result_backend

        return celery_app



def setup_mongo():
    ''' Initalize mongo database for fairscape server application
    '''

    mongo_config = get_mongo_config()
    mongo_client = mongo_config.CreateClient()

    # create database if not created 
    mongo_db = mongo_client[mongo_config.db]
    
    # create identifier collection
    identifier_collection = mongo_db[mongo_config.identifier_collection]

    # create user collection
    mongo_collection = mongo_db[mongo_config.user_collection]

    # create text index for 
    # db.identifier.createIndex( { name: "text", description: "text" } )
    identifier_collection.create_index([('description', 'text'), ('name', 'text')], name="description_text")

    # create index for identifiers
    identifier_collection.create_index([("@id", ASCENDING)])

    # TODO create index for provenance properties
    #

    # TODO recency of metadata publication
    #identifier_collection.create_index({})




def setup_minio():
    ''' Initalize minio buckets for fairscape server application
    '''

    minio_config = get_minio_config()
    minio_client = get_minio_client()

    # create default bucket
    print(minio_config.default_bucket)
    minio_client.make_bucket(minio_config.default_bucket)

    # create rocrate bucket
    print(minio_config.rocrate_bucket)
    minio_client.make_bucket(minio_config.rocrate_bucket)


