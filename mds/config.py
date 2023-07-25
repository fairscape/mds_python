from enum import Enum
from pydantic import (
    BaseSettings,
    BaseModel
)
from typing import (
    Optional
)
import os
import pathlib
from urllib.parse import quote_plus
from pymongo import MongoClient
import minio
from functools import lru_cache

import casbin
import casbin_sqlalchemy_adapter

#AUTH_ENABLED = bool(os.environ.get("MDS_AUTH_ENABLED", "True"))

def setup_mongo():
    mongo_config = get_mongo()
    mongo_client = mongo_config.CreateClient()
    # create database if not created 

    # create identifier collection

    # create text index for 
    # db.stores.createIndex( { name: "text", description: "text" } )
    

@lru_cache()
def get_mongo_config():
    return MongoConfig(
        host= os.environ.get("MONGO_HOST", "localhost"),
        port= os.environ.get("MONGO_PORT", "27017"),
        user= os.environ.get("MONGO_ACCESS_KEY", "root"),
        password= os.environ.get("MONGO_SECRET_KEY", "rootpass"),
        db= os.environ.get("MONGO_DATABASE", "fairscape"),
        collection= os.environ.get("MONGO_COLLECTION", "mds")
    )

@lru_cache()
def get_mongo_client():
    mongo_config = get_mongo_config()
    return mongo_config.CreateClient()


@lru_cache()
def get_minio():
    return MinioConfig(
        uri= os.environ.get("MINIO_URI"),
        user= os.environ.get("MINIO_BUCKET"),
        password= os.environ.get("MINIO_ACCESS_KEY"),
        default_bucket= os.environ.get("MINIO_SECRET_KEY"), 
        secure= bool(os.environ.get("MINIO_SECURE", False)),
    )


@lru_cache()
def get_casbin_config():
    return CasbinConfig(
        policy_path= pathlib.Path(
            os.environ.get("CASBIN_POLICY", "casbin_policy.db")
        ),
        model_path= pathlib.Path(
            os.environ.get("CASBIN_MODEL", "./tests/restful_casbin.conf")
        )
    )

@lru_cache()
def get_casbin_enforcer():
    casbin_config = get_casbin_config()
    return casbin_config.CreateClient()
 
@lru_cache()
def get_jwt_secret():
    return os.environ.get("JWT_SECRET", "test-local-secret")


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
    user_collection: Optional[str] = "users"
    session_collection: Optional[str] = "sessions"

    class Config:
        validate_assignment=True


    def CreateClient(self):

        #connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.db}"
        connection_string = f"mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}"
        return MongoClient(connection_string)


class MinioConfig(BaseModel):
    uri: str 
    user: str 
    password: str 
    default_bucket: str 
    secure: bool

    def CreateClient(self):
        return minio.Minio(
                self.hostname, 
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
    model_path: pathlib.Path
    policy_path: pathlib.Path 
    #backend: CasbinAdapterEnum

    def CreateClient(self):
        adapter = casbin_sqlalchemy_adapter.Adapter(f'sqlite:///{self.policy_path}')
        casbinEnforcer = casbin.Enforcer(str(self.model_path), adapter)
        return casbinEnforcer


class FairscapeConfig(BaseSettings):
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


