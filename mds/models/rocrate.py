from zipfile import ZipFile
from fastapi.responses import StreamingResponse, FileResponse
import zipfile
from bson import SON
from pydantic import (
    BaseModel,
    constr,
    AnyUrl,
    Extra
)
import io
import os
import tempfile
import json
from pathlib import Path
from io import BytesIO
import boto3
from botocore.client import Config

from typing import Optional, Union, Dict, List, Generator
from datetime import datetime
import pymongo

from mds.fairscape_models.base import FairscapeBaseModel
from mds.fairscape_models.datasetcontainer import DatasetContainer
from mds.fairscape_models.dataset import Dataset
from mds.fairscape_models.software import Software
from mds.fairscape_models.computation import Computation

from mds.utilities.operation_status import OperationStatus

from mds.database.config import MINIO_BUCKET, MINIO_ROCRATE_BUCKET, MONGO_DATABASE, MONGO_COLLECTION



    


class ROCrate(FairscapeBaseModel):    
    metadataType: str = "Dataset"
    name: constr(max_length=64)
    metadataGraph: List[Union[Dataset, Software, Computation, DatasetContainer]]
    
    

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True    
        fields={                        
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            },
            "metadataGraph": {
                "title": "metadataGraph",
                "alias": "@graph"
            }
        }


    def validate_rocrate_objects(self, MongoClient: pymongo.MongoClient, MinioClient, Object) -> OperationStatus:
        
        mongo_database = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]


        # check that the rocrate doesn't already exist
        #if mongo_collection.find_one({"@id": self.guid}) != None:
        #    return OperationStatus(False, f"ROCrate {self.guid} already exists", 404)
        
        prefix, org, proj, creative_work_id = self.guid.split("/")
        
        compressed_object_path = f"{org}/{proj}/{creative_work_id}/{self.name}"
        print(compressed_object_path)
        
        # List instances of Dataset, Software in the ROCrate metadata
        object_instances_in_metadata = list(filter(
            lambda x: (x.metadataType == "https://w3id.org/EVI#Dataset" 
                       or x.metadataType == "https://w3id.org/EVI#Software"), 
                       self.metadataGraph)
        )

        # List full object paths specified in the ROCrate metadata
        object_paths_in_metadata = [obj_instance.contentUrl for obj_instance in object_instances_in_metadata]
        
        # List object names only from their full path                    
        objects_in_metadata = [Path(obj).name for obj in object_paths_in_metadata]
                
        try:
            object_instances_in_crate = MinioClient.list_objects(MINIO_ROCRATE_BUCKET, recursive=True)
            object_paths_in_crate = [obj_instance.object_name for obj_instance in object_instances_in_crate]            
            objects_in_crate = [Path(obj).name for obj in object_paths_in_crate]
            
            # Check if metadata objects exist in the crate
            if set(objects_in_metadata).issubset(set(objects_in_crate)):                
                
                # Upload the zip file for easier download
                """upload_operation = MinioClient.fput_object(
                    bucket_name=MINIO_BUCKET,
                    object_name=f"{compressed_object_path}.zip",  
                    file_path="/home/sadnan/PycharmProjects/mds_python/tests/guid_test_rocrate.zip",                 
                    #content_type="application/zip"
                )"""

                
                file_size = os.fstat(Object.fileno()).st_size
                print(file_size)
                

                #Upload the zip file for easier download
                """upload_operation = MinioClient.put_object(
                    bucket_name=MINIO_BUCKET,
                    object_name=f"{compressed_object_path}.zip",                    
                    data=Object,                
                    length=-1,
                    part_size= 5 * 1024 * 1024 ,
                    content_type="application/zip"
                    #metadata={"identifier": self.id, "name": self.name}
                )"""
                    




                


            else:
                missing_objects = set(objects_in_metadata) - set(objects_in_crate)
                # TODO: undo the unzip bucket upload
                return OperationStatus(False, f"exception validating objects in ROCrate: Missing {str(missing_objects)} in the crate", 404)            

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
        
                
        return OperationStatus(True, "", 200)
    
    
      
    def read_metadata(self, MongoClient: pymongo.MongoClient) -> OperationStatus:
        
        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]
        #return super().read(mongo_collection)


    
                




    def read(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

        try:            
            query = mongo_collection.find_one(
                {'@id': self.guid},
                projection={'_id': False}
            )
            print("SELF: ", self)
            print("QUERY: ", query)
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




def unzip_and_upload(MinioClient, Object) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file

    Returns:
        OperationStatus: Message
    """        

    try:            
        zip_contents = Object.read()
        with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:                                        
            for file_info in zip_file.infolist():
                file_contents = zip_file.read(file_info.filename)
                MinioClient.put_object(MINIO_ROCRATE_BUCKET, file_info.filename, io.BytesIO(file_contents), len(file_contents))

    except Exception as e:
        return OperationStatus(False, f"Exception uploading ROCrate: {str(e)}", 500)
        
    return OperationStatus(True, "", 200)

def remove_unzipped_crate(MinioClient, Object) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file

    Returns:
        OperationStatus: Message
    """        

    try:            
        #zip_contents = Object.read()
        with zipfile.ZipFile(Object, "r") as zip_file:                                        
            for file_info in zip_file.infolist():
                #print(file_info.filename)                
                MinioClient.remove_object(MINIO_ROCRATE_BUCKET, file_info.filename)

    except Exception as e:
        return OperationStatus(False, f"Exception removing ROCrate: {str(e)}", 404)
        
    return OperationStatus(True, "", 200)






def get_metadata_from_crate(minio_client, Object, crate_file_name):
    """Extract metadata from the unzipped ROCrate onto MinIO

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file
        crate_file_name (str): File name to look for

    Returns:
        _type_: content from the crate_file_name
    """
    
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



def get_object_info_from_crate(rocrate_id: str, MongoClient: pymongo.MongoClient):
        
    mongo_db = MongoClient[MONGO_DATABASE]
    MongoCollection = mongo_db[MONGO_COLLECTION]

    try:
        
        query_projection = {'_id': False}
        # run the query
        query = MongoCollection.find_one(
            {'@id': rocrate_id},
            projection=query_projection
        )
    
        if query:
            # update class with values from database
            for key, value in query.items():
                if key == "distribution":                    
                    rocrate_bucket = value[0]['uncompressedRocrateBucket']
                    file_list = value[0]['uncompressed_ObjectPaths']

                    return rocrate_bucket, file_list
        else:
            return "", []

    # catch all exceptions
    except Exception as e:
        raise Exception(e)



def package_as_zip(bucket_name: str, object_loc_in_bucket, minio_client):

    zip_file_path = "/home/sadnan/rocrate_zipped.zip"
    
    try:
        with ZipFile(zip_file_path, 'w') as zip_file:
            for obj_path in object_loc_in_bucket:
                
                print(Path(obj_path), Path(obj_path).name)
                
                file_path = Path(obj_path).name
                local_file_path = f"/tmp/{file_path}"
                
                minio_client.fget_object(bucket_name=bucket_name, object_name=obj_path, file_path=local_file_path)
                
                zip_file.write(local_file_path, Path(obj_path).name)                
                
                os.remove(local_file_path)

        headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": "attachment;filename=test rocrate.zip"
        }
        
        return StreamingResponse(get_data_from_file(zip_file_path), headers=headers, media_type="application/zip")        
        
    except Exception as e:
        raise Exception("Unable to zip objects: ", e)




def package_as_zip_without_saving(bucket_name: str, object_loc_in_bucket, minio_client):

    zip_file_path = "/home/sadnan/rocrate_zipped.zip"
    zip_data = io.BytesIO()
    
    try:
        with ZipFile(zip_data, 'w') as zip_file:
            for obj_path in object_loc_in_bucket:
                
                print(Path(obj_path), Path(obj_path).name)
                
                file_path = Path(obj_path).name
                
                
                obj_data = minio_client.get_object(bucket_name=bucket_name, object_name=obj_path)
                
                zip_file.writestr(file_path, obj_data.read())                                

        headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": "attachment;filename=test rocrate.zip"
        }
        
        return StreamingResponse(get_data_from_stream(zip_data), headers=headers, media_type="application/zip")        

    except Exception as e:
        raise Exception("Unable to zip objects: ", e)



def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()
    


def get_data_from_stream(file_data) -> Generator:
    #with open(file=file_data, mode="rb") as file_like:
        yield file_data.getvalue()




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

        
    