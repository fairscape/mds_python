from zipfile import ZipFile
import zipfile
from bson import SON
from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)
import io
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
        uploads the file and ammends the dataDownload metadata and dataset metadata
        """


        # TODO format the contentUrl
        # prefix, org, proj, creative_work_id, identifier  =self.id.split("/")
        prefix, org, proj, creative_work_id  =self.guid.split("/")

        
        
        contentUrl = f"{org}/{proj}/{creative_work_id}/{self.name}"

        



        datasets = list(filter(
            lambda x: x.metadataType == "https://w3id.org/EVI#Dataset", self.metadataGraph
        ))
        
                    
        print("datasets: ", datasets)

        for i in datasets:
            print(i.contentUrl)


        
        




        
        # TODO run sha256 as a background task
        # create sha256 for object

        # upload object to minio
        try:
            upload_operation = MinioClient.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=contentUrl,
                data=Object,
                length=-1,
                part_size=10 * 1024 * 1024,
                #metadata={"identifier": self.id, "name": self.name}
            )

            # get the size of the file from the stats
            result_stats = MinioClient.stat_object(
                bucket_name=MINIO_BUCKET,
                object_name=contentUrl
            )

            
        #except Exception as e:
        #    return OperationStatus(False, f"exception uploading: {str(e)}", 500)

        #return OperationStatus(True, "", 201)
    

        #try:
            # Initialize Minio clients
            src_client = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='testroot', aws_secret_access_key='testroot', verify=False)
            dst_client = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='testroot', aws_secret_access_key='testroot', verify=False)

            # Define source and destination buckets and key paths
            src_bucket = MINIO_BUCKET
            dst_bucket = 'uncompressed'
            zip_key = contentUrl

            # Download zip file from source bucket
            zip_obj = src_client.get_object(Bucket=src_bucket, Key=zip_key)
            zip_content = io.BytesIO(zip_obj['Body'].read())

            # Unzip and upload each file to destination bucket
            zipfile_obj = zipfile.ZipFile(zip_content)
            for file in zipfile_obj.namelist():                
                file_content = zipfile_obj.read(file)
                dst_client.put_object(Bucket=dst_bucket, Key=file, Body=file_content)
 
        except Exception as e:
            return OperationStatus(False, f"exception uploading: {str(e)}", 500)

        return OperationStatus(True, "", 201)
   

