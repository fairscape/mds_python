from fastapi.responses import StreamingResponse

import uuid
import zipfile
import re
import hashlib

from mds.config import get_ark_naan
from pydantic import (
    Field,
    constr,
#   computed_field
)

from mds.config import (
    get_minio_config,
    get_minio_client,
#    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
)
from typing import (
    Optional, 
    Union, 
    Dict, 
    List, 
    Generator
)
import hashlib
import json
import re

import io
import os
from pathlib import Path
from io import BytesIO
import zipfile
from zipfile import ZipFile


from datetime import datetime
import pymongo

from mds.models.fairscape_base import FairscapeBaseModel
from mds.utilities.operation_status import OperationStatus

from mds.database.config import MINIO_BUCKET, MINIO_ROCRATE_BUCKET, MONGO_DATABASE, MONGO_COLLECTION
import sys
import logging

# setup logger for minio operations
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
rocrate_logger = logging.getLogger("rocrate")


DATASET_TYPE = "Dataset"
DATASET_CONTAINER_TYPE = "DatasetContainer"
SOFTWARE_TYPE = "Software"
COMPUTATION_TYPE = "Computation"
ROCRATE_TYPE = "ROCrate"

class ROCrateDataset(FairscapeBaseModel):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    author: str = Field(max_length=64)
    datePublished: str = Field(...)
    version: str = Field(default="0.1.0")
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[Union[str, dict]] = Field(alias="schema", default=None)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedByComputation: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = Field(default=None)


class ROCrateDatasetContainer(FairscapeBaseModel): 
    metadataType: Optional[str] = Field(
        default="https://w3id.org/EVI#Dataset", 
        alias="@type"
        )
    additionalType: Optional[str] = Field(default="DatasetContainer")
    name: str
    version: str = Field(default="0.1.0")
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedByComputation: Optional[List[str]] = Field(default=[])
    hasPart: Optional[List[str]] = Field(default=[])
    isPartOf: Optional[List[str]] = Field(default=[])


    def validate_crate(self, PassedCrate)->None:
        # for all linked IDs they must be

        # hasPart/isPartOf must be inside the crate or a valid ark

        # lookup ark if NAAN is local

        # if remote, take as valid
        pass


class ROCrateSoftware(FairscapeBaseModel): 
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Software")
    additionalType: Optional[str] = Field(default=SOFTWARE_TYPE)
    author: str = Field(min_length=4, max_length=64)
    dateModified: str
    version: str = Field(default="0.1.0")
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = Field(default=None)


class ROCrateComputation(FairscapeBaseModel):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Computation")
    additionalType: Optional[str] = Field(default=COMPUTATION_TYPE)
    runBy: str
    dateCreated: str
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default=None)
    usedSoftware: Optional[List[str]] = Field(default=[])
    usedDataset: Optional[List[str]] = Field(default=[])
    generated: Optional[List[str]] = Field(default=[])


class ROCrate(FairscapeBaseModel):
    metadataType: Optional[str] = Field(default="https://schema.org/Dataset", alias="@type")
    additionalType: Optional[str] = Field(default=ROCRATE_TYPE)
    name: constr(max_length=100)
    sourceOrganization: Optional[str] = Field(default=None)
    metadataGraph: List[Union[
        ROCrateDataset,
        ROCrateSoftware,
        ROCrateComputation,
        ROCrateDatasetContainer
    ]] = Field(alias="@graph", discriminator='additionalType')

 #   @computed_field(alias="@id")
 #   @property
    def guid(self) -> str:

        # remove trailing whitespace 
        cleaned_name = re.sub('\s+$', '', self.name)

        # remove restricted characters
        url_name = re.sub('\W', '', cleaned_name.replace('', '-'))

        # add md5 hash digest on remainder of metadata
        sha_256_hash = hashlib.sha256()

        # use a subset of properties for hash digest
        digest_dict = {
            "name": self.name,
            "@graph": [model.model_dump_json(by_alias=True) for model in self.metadataGraph]
        }
        encoded = json.dumps(digest_dict, sort_keys=True).encode()
        sha_256_hash.update(encoded)
        digest_string = sha_256_hash.hexdigest()

        return f"ark:{get_ark_naan()}/rocrate-{url_name}-{digest_string[0:10]}"


    def entailment(self):
        """ Run entailment on EVI Provenance properties
        """

        computations = list(filter(lambda x: x.additionalType == "Computation", self.metadataGraph))

        def filterCrateByGUID(guid):
            return list(filter(lambda x: x.guid==guid, self.metadataGraph))

        def inverseUsedDataset(used_dataset_guid, computation_guid):
            used_dataset_list = filterCrateByGUID(used_dataset_guid)
            
            # update each dataset as 
            for used_dataset in used_dataset_list:
                used_dataset.usedByComputation.append(computation_guid)

        def inverseUsedSoftware(used_software_guid, computation_guid):
            used_software_list = filterCrateByGUID(used_software_guid) 
            
            for used_software in used_software_list:
                used_software.usedByComputation.append(computation_guid)


        def inverseGenerated(generated_guid, computation_guid):
            generated_list = filterCrateByGUID(generated_guid)

            for generated_element in generated_list:
                generated_element.generatedBy.append(computation_guid)


        for computation_element in computations:

            [ 
                inverseUsedDataset(used_dataset, computation_element.guid) for 
                used_dataset in computation_element.usedDataset
                ]

            [ 
                inverseUsedSoftware(used_software, computation_element.guid) for 
                used_software in computation_element.usedSoftware
                ]

            [ 
                inverseGenerated(generated, computation_element.guid) for 
                generated in computation_element.generated
                ]


    def validate_rocrate_object_reference(
            self, 
            TransactionFolder, 
            CrateName
            ) -> OperationStatus:

        minio_config = get_minio_config()
        minio_client = get_minio_client()


        archived_object_path = f"{TransactionFolder}/{CrateName}"


        # List instances of Dataset, Software in the ROCrate metadata
        object_instances_in_metadata = list(filter(
            lambda x: (x.additionalType == "Dataset"
                       or x.additionalType == "Software"),
            self.metadataGraph)
        )

        # List full object paths specified in the ROCrate metadata
        objects_in_metadata = [ 
            Path(metadata_elem.contentUrl).name for metadata_elem in 
            object_instances_in_metadata if metadata_elem.contentUrl is not None
            ]

        rocrate_logger(f"Parsing RO-CRATE objects={objects_in_metadata}")


        # Retrieve name of rocrate root directory


        try:
            object_instances_in_crate = minio_client.list_objects(
                minio_config.rocrate_bucket, 
                prefix=f"{TransactionFolder}", 
                recursive=True
                )

            object_paths_in_crate = [
                obj_instance.object_name for obj_instance in object_instances_in_crate
                ]
            objects_in_crate = [
                Path(obj).name for obj in object_paths_in_crate
                ]

            # Check if metadata objects exist in the crate
            if set(objects_in_metadata).issubset(set(objects_in_crate)):
                # calculate filesize
                # file_size = os.fstat(Object.fileno()).st_size
                # print(file_size)

                # insert the metadata onto the mongo metadata store
                self.distribution = {
                    "extractedROCrateBucket": minio_config.default_bucket,
                    "archivedROCrateBucket": minio_config.rocrate_bucket,
                    "extractedObjectPath": object_paths_in_crate,
                    "archivedObjectPath": f"{archived_object_path}.zip"
                }

                return OperationStatus(True, "", 200)

            else:
                missing_objects = set(objects_in_metadata) - set(objects_in_crate)
                return OperationStatus(
                    False,
                    f"ROCrate ERROR: Missing Objects {str(missing_objects)}",
                    404
                    )

        except Exception as e:
            return OperationStatus(
                False, 
                f"exception validating objects in ROCrate: {str(e)}", 
                500
                )



def UploadZippedCrate(
        MinioClient, 
        ZippedObject, 
        BucketName, 
        TransactionFolder: uuid.UUID, 
        Filename: str,
        GUID: str
        ) -> str:

    #source_filepath = Path(ZippedObject.filename).name
    upload_filepath = Path(str(TransactionFolder)) / Path(Filename)
    
    upload_result = MinioClient.put_object(
        bucket_name=BucketName, 
        object_name=str(upload_filepath), 
        data=ZippedObject, 
        metadata={"guid": GUID},
        length=-1,
        part_size= 5 * 1024 * 1024 ,
        content_type="application/zip"
        )                

    # log upload of zipped rocrate
    rocrate_logger.info(
        "message='Uploaded file to minio' " +
        f"object_name='{upload_result.object_name}' " +
        f"object_etag='{upload_result.etag}'"
        )

    return upload_result.object_name


def UploadExtractedCrate(
        MinioClient, 
        ZippedObject, 
        BucketName: str, 
        TransactionFolder: str
        ) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file
        ROCrateBucketName (str): Name of S3 Bucket to upload zip archive of ROCrate

    Returns:
        OperationStatus: Message
    """
 
    try:        
        zip_contents = ZippedObject.read()
            
        with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:
            for file_info in zip_file.infolist():
                file_contents = zip_file.read(file_info.filename)

                # TODO the source filepath will not start at the root of the rocrate
                # but rather the full passed filename
                source_filepath = Path(file_info.filename)
                upload_filepath = Path(TransactionFolder) / source_filepath

                upload_result = MinioClient.put_object(
                    bucket_name= BucketName, 
                    object_name=str(upload_filepath), 
                    data=io.BytesIO(file_contents), 
                    length=len(file_contents)
                    )

                rocrate_logger.info(
                    "message='Uploaded file to minio' " +
                    f"object_name='{upload_result.object_name}' " +
                    f"object_etag='{upload_result.etag}'"
                    )

    except Exception as e:
        return OperationStatus(False, f"Exception uploading ROCrate: {str(e)}", 500)

    return OperationStatus(True, "", 200)



def remove_unzipped_crate(MinioClient, BucketName: str, Object) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file

    Returns:
        OperationStatus: Message
    """

    # TODO fix for path refactor

    try:
        # zip_contents = Object.read()
        with zipfile.ZipFile(Object, "r") as zip_file:
            for file_info in zip_file.infolist():
                # print(file_info.filename)
                MinioClient.remove_object(
                    bucket_name=BucketName, 
                    object_name=file_info.filename
                    )

    except Exception as e:
        return OperationStatus(False, f"Exception removing ROCrate: {str(e)}", 404)

    return OperationStatus(True, "", 200)


def GetMetadataFromCrate(MinioClient, BucketName, TransactionFolder, CratePath) -> dict:
    """Extract metadata from the unzipped ROCrate onto MinIO

    Args:
        MinioClient (Any): MinIO client
        BucketName (str): name for bucket to search for the crate metadata
        TransactionFolder (str): UUID for this transaction 
        CratePath (str): name of expanded crate path

    Returns:
        ro_crate_json (dict): contents of the ro-crate-metadata.json file as a dictionary
    """

    try:
        # List all objects in the bucket
        ro_crate_response = MinioClient.get_object(
            bucket_name= BucketName, 
            object_name=f"{TransactionFolder}/{CratePath}/ro-crate-metadata.json", 
            )

        # read all metadata as json
        ro_crate_json = ro_crate_response.read()

        # TODO try to parse

        return ro_crate_json

    except Exception as e:
        raise Exception(f"ROCRATE ERROR: ro-crate-metadata.json not found exception={str(e)}")


def ListROCrates(rocrate_collection: pymongo.collection.Collection):
    """ List all ROCrates uploaded to FAIRSCAPE
    """

    rocrate_cursor = rocrate_collection.find(
        filter={"additionalType": ROCRATE_TYPE},
        projection={
            "@id": 1, 
            "name": 1, 
            "keywords": 1,
            "description": 1,
            "sourceOrganization": 1
            }
    )
    query_results = { "rocrates": list(rocrate_cursor) }
    rocrate_cursor.close()
    return query_results



def zip_extracted_rocrate(bucket_name: str, object_loc_in_bucket, minio_client):

    zip_data = io.BytesIO()

    try:
        with ZipFile(zip_data, 'w') as zip_file:
            for obj_path in object_loc_in_bucket:
                file_path = Path(obj_path).name
                obj_data = minio_client.get_object(bucket_name=bucket_name, object_name=obj_path)
                zip_file.writestr(file_path, obj_data.read())

        headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": "attachment;filename=downloaded-rocrate.zip"
        }

        return StreamingResponse(get_data_from_stream(zip_data), headers=headers, media_type="application/zip")

    except Exception as e:
        raise Exception("Unable to zip objects: ", e)


def zip_archived_rocrate(bucket_name: str, object_loc_in_bucket, minio_client):

    headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": f"attachment;filename=downloaded-rocrate.zip"
    }

    file_stream = minio_client.get_object(bucket_name=bucket_name, object_name=object_loc_in_bucket).read()

    return StreamingResponse(generator_iterfile(file_stream), headers=headers, media_type="application/zip")


# generator function to iterate over that file-like object
def generator_iterfile(file_stream) -> Generator:
    yield file_stream

def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()


def get_data_from_stream(file_data) -> Generator:
    yield file_data.getvalue()



def get_metadata_by_id(rocrate_collection: pymongo.collection, rocrate_id):
    try:
        # ignore _id in mongo documents
        query_projection = {'_id': False}
        # find rocrate metadata by the unique @id
        query = rocrate_collection.find_one(
            {'@id': rocrate_id},
            projection=query_projection
        )

    except Exception as e:
        raise Exception(e)
        
    if query:
        return query
        #try:
        #    parsed_crate = ROCrate(**query)
        #    return parsed_crate
        #except Exception as e:
        #    raise Exception(message=f"ROCRATE Metadata not valid: {str(e)}")
    
    else:
        raise Exception(message=f"ROCRATE NOT FOUND: {str(query)}")


def PublishROCrateMetadata(
        rocrate: ROCrate, 
        rocrate_collection: pymongo.collection.Collection
        ):  
    """ Insert ROCrate metadata into mongo rocrate collection
    """

    rocrate_json = rocrate.model_dump(by_alias=True)
    insert_result = rocrate_collection.insert_one(rocrate_json)
    if insert_result.inserted_id is None:
        return False
    else:
        return True


def PublishProvMetadata(rocrate: ROCrate, identifier_collection: pymongo.collection.Collection):
    """ Insert ROCrate metadata and metadata for all identifiers into the identifier collection
    """

    # for every element in the rocrate model dump json
    insert_metadata = [ prov.model_dump(by_alias=True) for prov in rocrate.metadataGraph  ]
    # insert rocrate json into identifier collection
    insert_metadata.append(rocrate.model_dump(by_alias=True))

    # insert all identifiers into the identifier collection
    insert_result = identifier_collection.insert_many(insert_metadata)

    if len(insert_result.inserted_ids) != len(insert_metadata):
        return False
    else:
        return True

