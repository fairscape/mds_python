from zipfile import ZipFile
import zipfile
from bson import SON
from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)
import io
import json
from pathlib import Path
from io import BytesIO
import boto3
from botocore.client import Config

from typing import Optional, Union, Dict, List
from datetime import datetime
import pymongo

from mds.models.fairscape_base import *
from mds.models.compact import *

from mds.fairscape_models.datasetcontainer import DatasetContainer
from mds.fairscape_models.dataset import Dataset
from mds.fairscape_models.software import Software
from mds.fairscape_models.computation import Computation

from mds.utilities.operation_status import OperationStatus

from mds.database.config import MINIO_BUCKET, MINIO_ROCRATE_BUCKET, MONGO_DATABASE, MONGO_COLLECTION



    


class ROCrate(BaseModel):
    guid: str
    context: Union[str, Dict[str,str]] = {
                "@vocab": "https://schema.org/",
                "evi": "https://w3id.org/EVI#"
            }
    metadataType: str = "Dataset"
    name: constr(max_length=64)
    metadataGraph: List[Union[Dataset, Software, Computation, DatasetContainer]]
    
    

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True    
        fields={
            "context": {
                "title": "context",
                "alias": "@context"
            },
            "guid": {
                "title": "guid",
                "alias": "@id"
            },
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            },
            "name": {
                "title": "name"
            },
            "metadataGraph": {
                "title": "metadataGraph",
                "alias": "@graph"
            }
        }

    
    #_validate_guid = validator('id', allow_reuse=True)(validate_ark)

    def validate_rocrate_objects(self, MongoClient: pymongo.MongoClient, MinioClient, Object) -> OperationStatus:
        
        mongo_database = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]


        # check that the rocrate doesn't already exist
        #if mongo_collection.find_one({"@id": self.guid}) != None:
        #    return OperationStatus(False, f"ROCrate {self.guid} already exists", 404)
        
        prefix, org, proj, creative_work_id = self.guid.split("/")
        
        compressed_object_path = f"{org}/{proj}/{creative_work_id}/{self.name}"
        #print(compressed_object_path)
        
        #print(self.guid)
        #print(self.metadataGraph)
        
        # List instances of Dataset, Software in the ROCrate metadata
        object_instances_in_metadata = list(filter(
            lambda x: (x.metadataType == "https://w3id.org/EVI#Dataset" 
                       or x.metadataType == "https://w3id.org/EVI#Software"), 
                       self.metadataGraph)
        )

        # List object paths specified in the ROCrate metadata
        object_paths_in_metadata = [obj_instance.contentUrl for obj_instance in object_instances_in_metadata]
        #print(object_paths_in_metadata)
        # List object names only from their full path                    
        objects_in_metadata = [Path(obj).name for obj in object_paths_in_metadata]
        #print(objects_in_metadata)
        
        
        try:
            object_instances_in_crate = MinioClient.list_objects(MINIO_ROCRATE_BUCKET, recursive=True)
            object_paths_in_crate = [obj_instance.object_name for obj_instance in object_instances_in_crate]
            #print("Object paths in crate: ", object_paths_in_crate) 
            objects_in_crate = [Path(obj).name for obj in object_paths_in_crate]
            #print(objects_in_crate)
            if set(objects_in_metadata).issubset(set(objects_in_crate)):
                print("is a subset")
                
                #  
                upload_operation = MinioClient.put_object(
                    bucket_name=MINIO_BUCKET,
                    object_name=compressed_object_path,
                    data=Object,
                    length=-1,
                    part_size=10 * 1024 * 1024,
                    #metadata={"identifier": self.id, "name": self.name}
                )
            else:
                missing_objects = set(objects_in_metadata) - set(objects_in_crate)
                return OperationStatus(False, f"exception validating objects in ROCrate: Missing {str(missing_objects)} in the crate", 500)            

        except Exception as e:
            return OperationStatus(False, f"exception validating objects in ROCrate: {str(e)}", 500)    

        # insert the metadata onto the mongo metadata store
        insert_result = mongo_collection.insert_one(self.dict(by_alias=True))

        update_result = mongo_collection.update_one(
            {"@id": self.guid},
            {"$addToSet": {
                "distribution": SON(
                    [("@id", self.guid), 
                     ("@type", "Dataset"), 
                     ("name", self.name),                      
                     ("uncompressedRocrateBucket", MINIO_ROCRATE_BUCKET), 
                     ("compressedRocrateBucket", MINIO_BUCKET), 
                     ("uncompressed_ObjectPaths", object_paths_in_crate), 
                     ("compressedObjectPath", compressed_object_path)
                    ])}
            })
        
        
   
    
      



    def read(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

        try:            
            query = mongo_collection.find_one(
                {'@id': self.guid},
                projection={'_id': False}
            )
            print("SELF: ", self)
            #print("QUERY: ", query)
            if query:
                crate = ROCrate(**query)
                print(crate.name)
            
            # check that the results are no empty
            if query:
                # update class with values from database
                for k, value in query.items():
                    #print("\nkey :", k, "value :", value)
                    #setattr(self, k, value)
                    if k == "distribution":
                        print(value)
                        convert_dist = json.dumps(value)
                        dist = json.loads(convert_dist)
                        #print(dist[0]['uncompressedRocrateBucket'])
                        print(dist[0]['compressedRocrateBucket'])
                        #print(dist[0]['uncompressed_ObjectPaths'])
                        print(dist[0]['compressedObjectPath'])
                return OperationStatus(True, "", 200)
            else:
                return OperationStatus(False, "No record found", 404)

        # default exceptions for all mongo operations
        except pymongo.errors.CollectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        # except pymongo.errors.ConnectionError as e:
        #    return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)

        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Error Invalid Name: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Error Network Timeout: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)


        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)



def uncompress_upload_rocrate(MinioClient, Object) -> OperationStatus:
    """Accepts a compressed ROCrate consisting of objects, uncompress and upload them onto the object store.

    Args:
        MinioClient (Any): client for the object store
        Object (Any): Compressed ROCrate file in zip

    Returns:
        OperationStatus: Message
    """        
    # Uncompress objects in ROCrate and upload to the object store
    try:            
        zip_contents = Object.read()
        with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:                            
            # Upload each file into minio
            for file_info in zip_file.infolist():
                file_contents = zip_file.read(file_info.filename)
                MinioClient.put_object(MINIO_ROCRATE_BUCKET, file_info.filename, io.BytesIO(file_contents), len(file_contents))

    except Exception as e:
        return OperationStatus(False, f"exception uploading uncompressed rocrate: {str(e)}", 500)
        
    return OperationStatus(True, "", 201)


def get_metadata_from_crate(minio_client, Object, crate_file_name):
    
    with zipfile.ZipFile(Object, "r") as zip_ref: 
        file_names = zip_ref.namelist() 
            
        for file_name in file_names: 
            if file_name.endswith(crate_file_name): 
                return minio_client.get_object(MINIO_ROCRATE_BUCKET, file_name).read()
            


def list_rocrates(MongoClient: pymongo.MongoClient):

    mongo_db = MongoClient[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    
    cursor = mongo_collection.find(
        filter={"@type": "Dataset"},
        projection={"_id": False}
    )
    return {
        "rocrates": [{"@id": rocrate.get("@id"), "@type": "Dataset", "name": rocrate.get("name")}
                          for rocrate in cursor]}




def read_rocrate_metadata(MongoClient: pymongo.MongoClient, crate_id: str) -> dict:

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

                    
        query = mongo_collection.find_one(
            {'@id': crate_id},
            projection={'_id': False}
        )
            
            
            
            # check that the results are no empty
        if query:
                # update class with values from database                
            return query
        else:
            raise Exception(message=f"ROCRATE NOT FOUND: {str(query)}")

        