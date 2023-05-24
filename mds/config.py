from enum import Enum
from pydantic import (
    BaseSettings,
    BaseModel
)
from pathlib import Path

from urllib.parse import quote_plus
from pymongo import MongoClient
import minio


class MongoConfig(BaseModel):
    host: str 
    port: str 
    user: str 
    password: str 
    db: str 
    collection: str 

    def CreateClient(self) -> MongoClient:

        connection_string = f"mongodb://{quote_plus(self.user)}:" +
            f"{quote_plus(self.password)}@{self.host}:{self.port}/{self.db}"
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


class K8sComputeConfig(BaseModel):
    redis: RedisConfig

class RedisConfig(BaseModel):
    port: int
    uri: str
    broker_url: Optional[str]
    result_backend: Optional[str]


class DockerConfig(BaseModel):
    pass
    

class CasbinAdapterEnum(str, Enum):
    """ Choices for supported Backends for Casbin Model Storage
    """
    sqlite = "sqlite"

class CasbinConfig(BaseModel):
    config_path: Path
    policy_path: Path 
    #backend: CasbinAdapterEnum

    def CreateClient(self)
        adapter = casbin_sqlalchemy_adapter.Adapter(f'sqlite:///{self.policy_path}')
        casbinEnforcer = casbin.Enforcer('./mds/database/default_model.conf', adapter)


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

