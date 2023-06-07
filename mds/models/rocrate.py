from zipfile import ZipFile
import zipfile
from bson import SON
from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)
import io
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

from mds.database.config import MINIO_BUCKET


class ROCrate(BaseModel):
    guid: str
    context: Union[str, Dict[str,str]] = {
                "@vocab": "https://schema.org/",
                "evi": "https://w3id.org/EVI#"
            }
    metadataType: str = "https://w3id.org/EVI#ROCrate"
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
    
    def rocrate_transfer(self, MinioClient, Object) -> OperationStatus:
        """
        Uploads the file, uncompress and check if all contents mentioned 
        in the ROCrate are present in the crate 
        """

        prefix, org, proj, creative_work_id = self.guid.split("/")
        
        object_path = f"{org}/{proj}/{creative_work_id}/{self.name}"

        
        crate_files = list(filter(
            lambda x: (x.metadataType == "https://w3id.org/EVI#Dataset" 
                       or x.metadataType == "https://w3id.org/EVI#Software"), 
                       self.metadataGraph)
        )
                            
        for crate_file in crate_files:
            print(crate_file.contentUrl)


        # upload object to minio
        try:
            upload_operation = MinioClient.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_path,
                data=Object,
                length=-1,
                part_size=10 * 1024 * 1024,
                #metadata={"identifier": self.id, "name": self.name}
            )

            # get the size of the file from the stats
            result_stats = MinioClient.stat_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_path
            )

            
            # Initialize Minio clients
            src_client = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='testroot', aws_secret_access_key='testroot', verify=False)
            dst_client = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='testroot', aws_secret_access_key='testroot', verify=False)

            # Define source and destination buckets and key paths
            src_bucket = MINIO_BUCKET
            dst_bucket = 'cratecontent'
            zip_key = object_path

            # Download zip file from source bucket
            zip_obj = src_client.get_object(Bucket=src_bucket, Key=zip_key)
            #zip_obj = MinioClient.get_object(bucket_name=src_bucket, object_name=zip_key)
            
            zip_content = io.BytesIO(zip_obj['Body'].read())

            # Unzip and upload each file to destination bucket
            zipfile_obj = zipfile.ZipFile(zip_content)
            print(zipfile_obj.namelist())
            for file in zipfile_obj.namelist():                
                file_content = zipfile_obj.read(file)
                dst_client.put_object(Bucket=dst_bucket, Key=file, Body=file_content)
                #MinioClient.put_object(bucket_name=dst_bucket, 
                #                        object_name=file, 
                #                        data=file_content,
                #                        length=-1,
                #                        #part_size=10 * 1024 * 1024
                #                       )


            
            
        except Exception as e:
            return OperationStatus(False, f"exception uploading: {str(e)}", 500)

        return OperationStatus(True, "", 201)
   

    def attempt_transfer(self, MongoClient: pymongo.MongoClient, MinioClient, Object) -> OperationStatus:
        """
        Before attempting to transfer, unzip into a compressed rocrate
        """

        prefix, org, proj, creative_work_id = self.guid.split("/")
        
        object_path = f"{org}/{proj}/{creative_work_id}/{self.name}"

        # Filter all instances of Dataset and Software from ro-crate-metadata.json
        rocrate_metadata_components = list(filter(
            lambda x: (x.metadataType == "https://w3id.org/EVI#Dataset" 
                       or x.metadataType == "https://w3id.org/EVI#Software"), 
                       self.metadataGraph)
        )
        
        # List all Dataset and Software object references
        rocrate_metadata_objects = [Path(rocrate_component.contentUrl).name for rocrate_component in rocrate_metadata_components]
        print("Objects Referenced in the ro-crate-metadata.json\n", rocrate_metadata_objects)

        rocrate_archived_objects = []

        uncompress_bucket = 'cratecontent'        
        try:
            # Uncompress the rocrate and upload into object store
            zip_contents = Object.read()
            with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:
                # print(zip_file.namelist())
                rocrate_archived_objects = [Path(file).name for file in zip_file.namelist()]
                print(rocrate_archived_objects)                
                # Upload each file into minio
                for file_info in zip_file.infolist():
                    file_contents = zip_file.read(file_info.filename)
                    MinioClient.put_object(uncompress_bucket, file_info.filename, io.BytesIO(file_contents), len(file_contents))

            # check if all objects referenced in the metadata exist in the archived crate
            if not set(rocrate_metadata_objects) == set(rocrate_archived_objects):                
                return OperationStatus(False, f"All referenced objects are not in the crate", 500)

            # Proceed with uploading the rocrate archived file into minio
            MinioClient.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_path,
                data=Object,
                length=-1,
                part_size=10 * 1024 * 1024,
                #metadata={"identifier": self.id, "name": self.name}
            )

        except Exception as e:
            return OperationStatus(False, f"exception uploading: {str(e)}", 500)

        return OperationStatus(True, "", 201)
