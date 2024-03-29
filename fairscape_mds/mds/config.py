from enum import Enum
from pydantic import (
    BaseModel,
    Field
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



@lru_cache()
def cached_dotenv(env_path: str = '.env'):
    config = {
        **dotenv_values(env_path),
        **os.environ,
    }
    return config


@lru_cache()
def get_fairscape_config():
    
    config_values = cached_dotenv()

    server_mongo_config = MongoConfig.model_validate(
        {
            'host': config_values.get('MONGO_HOST'), 
            'port': config_values.get("MONGO_PORT"),
            'user': config_values.get('MONGO_ACCESS_KEY'),
            'password': config_values.get('MONGO_SECRET_KEY'),
            'db': config_values.get('MONGO_DATABASE'),
            'identifier_collection': config_values.get('MONGO_IDENTIFIER_COLLECTION'),
            'user_collection': config_values.get('MONGO_USER_COLLECTION'),
            'rocrate_collection': config_values.get('MONGO_ROCRATE_COLLECTION')
        }
        )

    server_minio_config = MinioConfig(
        host= config_values.get("MINIO_URI"),
        port=config_values.get("MINIO_PORT"),
        access_key = config_values.get("MINIO_ACCESS_KEY"),
        secret_key = config_values.get("MINIO_SECRET_KEY"),
        default_bucket= config_values.get("MINIO_DEFAULT_BUCKET"), 
        rocrate_bucket=config_values.get("MINIO_ROCRATE_BUCKET"),
        secure= bool(config_values.get("MINIO_SECURE")=="True"),
    )
    
    return FairscapeConfig(
            host = config_values.get('FAIRSCAPE_HOST'),
            port = config_values.get('FAIRSCAPE_PORT'),
            mongo = server_mongo_config,
            minio = server_minio_config
            )


@lru_cache()
def get_rdflib_config():
    return None


@lru_cache()
def get_rdflib_client():
    return None

 
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
        host= config_values.get("MINIO_URI"),
        port=config_values.get("MINIO_PORT"),
        access_key = config_values.get("MINIO_ACCESS_KEY"),
        secret_key = config_values.get("MINIO_SECRET_KEY"),
        default_bucket= config_values.get("MINIO_DEFAULT_BUCKET"), 
        rocrate_bucket=config_values.get("MINIO_ROCRATE_BUCKET"),
        secure= bool(config_values.get("MINIO_SECURE")=="True"),
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
            config_values.get("CASBIN_POLICY")
        ),
        casbin_model_path= pathlib.Path(
            config_values.get("CASBIN_MODEL")
        )
    )

@lru_cache()
def get_casbin_enforcer():
    casbin_config = get_casbin_config()
    return casbin_config.CreateClient()
 
@lru_cache()
def get_jwt_secret():
    config_values = cached_dotenv()
    return config_values.get("JWT_SECRET")

@lru_cache()
def get_ark_naan():
    # TODO return entire config object
    config_values= cached_dotenv()
    return config_values.get("ARK_NAAN", "59853")

#MongoDep = Annotated[pymongo.MongoClient, Depends(common_parameters)]
#CasbinDep = Annotated[casbin.Enforcer, Depends(get_casbin)]
#MinioDep = Annotated[minio.MinioClient, Depends(get_minio)]


class MongoConfig(BaseModel):
    host: Optional[str] = Field(default="localhost")
    port: Optional[str] = Field(default="27017")
    user: Optional[str] = Field(default="mongotestaccess")
    password: Optional[str] = Field(default="mongotestsecret")
    db: Optional[str] = Field(default="fairscape")
    identifier_collection: Optional[str] = Field(default="mds")
    rocrate_collection: Optional[str] = Field(default="rocrate")
    user_collection: Optional[str] = Field(default="users")
    session_collection: Optional[str] = Field(default="sessions")


    def CreateClient(self):

        #connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.db}"
        connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}/?authSource=admin"
        return MongoClient(connection_string)


class MinioConfig(BaseModel):
    host: Optional[str] = Field(default="localhost")
    port: Optional[str] = Field(default="9000")
    secret_key: Optional[str] = Field(default="")
    access_key: Optional[str] = Field(default="")
    default_bucket: Optional[str] = Field(default="mds")
    rocrate_bucket: Optional[str] = Field(default="rocrate")
    secure: Optional[bool] = Field(default=False)


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
    casbin_model_path: Optional[pathlib.Path] = Field(defaul= None) #=pathlib.Path("./deploy/casbin_model.conf"))
    policy_path: Optional[pathlib.Path] = Field(default=pathlib.Path("casbin_policy.db"))
    #backend: CasbinAdapterEnum

    def CreateClient(self):
        adapter = casbin_sqlalchemy_adapter.Adapter(f'sqlite:///{self.policy_path}') 
        casbinEnforcer = casbin.Enforcer(str(self.casbin_model_path), adapter)
        return casbinEnforcer


class FairscapeConfig(BaseModel):
    host: Optional[str] = Field(default='0.0.0.0')
    port: Optional[int] = Field(default=8080)
    mongo: MongoConfig
    minio: MinioConfig
#    compute: K8sComputeConfig
#    casbin: CasbinConfig


    def CreateMongoClient(self):
        return self.mongo.CreateClient() 
    
    def CreateMinioClient(self):
        return self.minio.CreateClient()


    def RunServer(self):
        uvicorn.run(
            'fairscape_mds.mds.app:app', 
            host=self.host, 
            port=self.port, 
            reload=True
            )


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


