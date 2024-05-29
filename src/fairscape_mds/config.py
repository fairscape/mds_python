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
import uvicorn

from dotenv import dotenv_values



@lru_cache()
def cached_dotenv(env_path: str = '.env'):
    config = {
        **dotenv_values(env_path),
        **os.environ,
    }
    return config

@lru_cache()
def get_mongo_config():
    mds_config = get_fairscape_config()
    return mds_config.mongo

@lru_cache()
def get_mongo_client():
    mds_config = get_fairscape_config()
    return mds_config.CreateMongoClient()

@lru_cache()
def get_minio_config():
    mds_config = get_fairscape_config()
    return mds_config.minio

@lru_cache()
def get_minio_client():
    mds_config = get_fairscape_config()
    return mds_config.CreateMinioClient()

@lru_cache()
def get_fairscape_url():
    return get_fairscape_config().url
    

@lru_cache()
def get_fairscape_config(env_path: str = '../deploy/local.env'):    
    config_values = cached_dotenv(env_path)

    server_mongo_config = MongoConfig.model_validate(
        {
            'host': config_values.get('FAIRSCAPE_MONGO_HOST'), 
            'port': config_values.get("FAIRSCAPE_MONGO_PORT", "27017"),
            'user': config_values.get('FAIRSCAPE_MONGO_ACCESS_KEY'),
            'password': config_values.get('FAIRSCAPE_MONGO_SECRET_KEY'),
            'db': config_values.get('FAIRSCAPE_MONGO_DATABASE'),
            'identifier_collection': config_values.get('FAIRSCAPE_MONGO_IDENTIFIER_COLLECTION'),
            'user_collection': config_values.get('FAIRSCAPE_MONGO_USER_COLLECTION'),
            'rocrate_collection': config_values.get('FAIRSCAPE_MONGO_ROCRATE_COLLECTION')
        }
        )

    server_minio_config = MinioConfig(
        host= config_values.get("FAIRSCAPE_MINIO_URI"),
        port=config_values.get("FAIRSCAPE_MINIO_PORT"),
        access_key = config_values.get("FAIRSCAPE_MINIO_ACCESS_KEY"),
        secret_key = config_values.get("FAIRSCAPE_MINIO_SECRET_KEY"),
        default_bucket= config_values.get("FAIRSCAPE_MINIO_DEFAULT_BUCKET"), 
        rocrate_bucket=config_values.get("FAIRSCAPE_MINIO_ROCRATE_BUCKET"),
        secure= bool(config_values.get("FAIRSCAPE_MINIO_SECURE")=="True"),
    )

    server_redis_config = RedisConfig(
        port= config_values.get("FAIRSCAPE_REDIS_PORT", 6379),
        hostname = config_values.get("FAIRSCAPE_REDIS_HOST", 'localhost'),
        username= config_values.get("FAIRSCAPE_REDIS_USERNAME"),
        password= config_values.get("FAIRSCAPE_REDIS_PASSWORD"),
        database= config_values.get("FAIRSCAPE_REDIS_DATABASE"),
        result_database = config_values.get("FAIRSCAPE_REDIS_RESULT_DATABASE") 
    )

    # TODO support multiple NAANs
    
    return FairscapeConfig(
            host = config_values.get('FAIRSCAPE_HOST'),
            port = config_values.get('FAIRSCAPE_PORT'),
            jwtSecret = config_values.get('FAIRSCAPE_JWT_SECRET', 'testjwtsecret'),
            passwordSalt = config_values.get('FAIRSCAPE_PASSWORD_SALT', 'testsalt'),
            NAAN = config_values.get('FAIRSCAPE_NAAN', '59852'),
            url = config_values.get("FAIRSCAPE_URL"),
            mongo = server_mongo_config,
            minio = server_minio_config,
            redis = server_redis_config,
            )


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
    port: Optional[int] = Field(default=6379)
    hostname: Optional[str] = Field(default='localhost')
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    database: Optional[int] = Field(default=0)
    result_database: Optional[int] = Field(default=1)

    def getBrokerURL(self):
        if self.username and self.password:
            return f'redis://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}'
        else:
            return f'redis://{self.hostname}:{self.port}/{self.database}'


class K8sComputeConfig(BaseModel):
    redis: RedisConfig
    

class FairscapeConfig(BaseModel):
    host: Optional[str] = Field(default='0.0.0.0')
    port: Optional[str] = Field(default='8080')
    jwtSecret: str 
    passwordSalt: str 
    NAAN: Optional[str] = Field(default = '59852')
    url: Optional[str] = Field(default = "http://localhost:8080/")
    mongo: MongoConfig
    minio: MinioConfig
    redis: Optional[RedisConfig]


    def CreateMongoClient(self):
        return self.mongo.CreateClient() 
    
    def CreateMinioClient(self):
        return self.minio.CreateClient()

    def RunServer(self):
        uvicorn.run(
            'fairscape_mds.app:app', 
            host=self.host, 
            port=int(self.port), 
            reload=True
            )


    def StartWorker(self):
        celery_app = Celery('compute', include="mds.compute.tasks")
        app.conf.broker_url = self.compute.redis.broker_url
        app.conf.result_backend = self.compute.redis.result_backend

        return celery_app



    def SetupMongo(self):
        ''' Initalize mongo database for fairscape server application
        '''
        mongo_client = self.CreateMongoClient()

        # create database if not created 
        mongo_db = mongo_client[self.mongo.db]
        
        # create identifier collection
        identifier_collection = mongo_db[self.mongo.identifier_collection]

        # create user collection
        mongo_collection = mongo_db[self.mongo.user_collection]

        # create text index for 
        # db.identifier.createIndex( { name: "text", description: "text" } )
        identifier_collection.create_index([('description', 'text'), ('name', 'text')], name="description_text")

        # create index for identifiers
        identifier_collection.create_index([("@id", ASCENDING)])

        # TODO create index for provenance properties

        # TODO recency of metadata publication
        #identifier_collection.create_index([])


    def SetupMinio(self):
        ''' Initalize minio buckets for fairscape server application
        '''

        minio_client = self.CreateMinioClient()

        try:
            # create default bucket
            minio_client.make_bucket(self.minio.default_bucket)

        except minio.S3Error as e:
            pass


        try:
            # create rocrate bucket
            minio_client.make_bucket(self.minio.rocrate_bucket)
        except minio.S3Error as e:
            pass

