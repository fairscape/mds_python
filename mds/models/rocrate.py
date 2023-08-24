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
import logging

# setup logger for minio operations
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
    usedBy: Optional[List[str]] = Field(default=[])
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
    usedBy: Optional[List[str]] = Field(default=[])
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
                used_dataset.usedBy.append(computation_guid)

        def inverseUsedSoftware(used_software_guid, computation_guid):
            used_software_list = filterCrateByGUID(used_software_guid) 
            
            for used_software in used_software_list:
                used_software.usedBy.append(computation_guid)


        def inverseGenerated(generated_guid, computation_guid):
            generated_list = filterCrateByGUID(generated_guid)

            for generated_element in generated_list:
                generated_element.generatedBy.append(computation_guid)


        for computation_element in computations:
            #used_datasets = computation.usedDatasets
            #used_software = computation.usedSoftware
            #  generated = computation.generated

            [ inverseUsedDataset(used_dataset.guid, computation_element.guid) for used_dataset in computation_element.usedDatasets]
            [ inverseUsedSoftware(used_software.guid, computation_element.guid) for used_software in computation_element.usedSoftware]
            [ inverseGenerated(generated.guid, computation_element.guid) for generated in computation_element.generated]


    def validate_rocrate_object_reference(self, Object) -> OperationStatus:

        mongo_config = get_mongo_config()
        mongo_client = get_mongo_client()
        mongo_db = mongo_client[mongo_config.db]
        rocrate_collection = mongo_db[mongo_config.rocrate_collection]

        minio_config = get_minio_config()
        minio_client = get_minio_client()

        # check that the rocrate doesn't already exist
        # if mongo_collection.find_one({"@id": self.guid}) != None:
        #    return OperationStatus(False, f"ROCrate {self.guid} already exists", 404)

        _, creative_work_id = self.guid.split("/")
        archived_object_path = f"{creative_work_id}/{self.name}"


        # List instances of Dataset, Software in the ROCrate metadata
        object_instances_in_metadata = list(filter(
            lambda x: (x.additionalType == "Dataset"
                       or x.additionalType == "Software"),
            self.metadataGraph)
        )

        # List full object paths specified in the ROCrate metadata
        object_paths_in_metadata = [obj_instance.contentUrl for obj_instance in object_instances_in_metadata]
        #print(object_paths_in_metadata)
        # List object names only from their full path                    
        objects_in_metadata = [Path(obj).name for obj in object_paths_in_metadata]
        #print(objects_in_metadata)


        # Retrieve name of rocrate root directory
        rocrate_root_dir = ''
        try:
            with zipfile.ZipFile(Object) as archive:
                if archive.namelist():
                    rocrate_root_dir = Path(archive.namelist()[0]).parent.joinpath('')

        except zipfile.BadZipFile as e:
            return OperationStatus(False, f"exception validating objects in ROCrate: {str(e)}", 500)


        try:
            object_instances_in_crate = minio_client.list_objects(
                minio_config.rocrate_bucket, 
                prefix=f"{rocrate_root_dir}", 
                recursive=True
                )

            object_paths_in_crate = [obj_instance.object_name for obj_instance in object_instances_in_crate]
            objects_in_crate = [Path(obj).name for obj in object_paths_in_crate]

            # Check if metadata objects exist in the crate
            if set(objects_in_metadata).issubset(set(objects_in_crate)):
                file_size = os.fstat(Object.fileno()).st_size
                # print(file_size)

                # Upload the zip file for easier download
                minio_client.put_object(
                    bucket_name=minio_config.default_bucket,
                    object_name=f"{archived_object_path}.zip",
                    data=Object,                
                    length=-1,
                    part_size= 5 * 1024 * 1024 ,
                    content_type="application/zip"
                )
            else:
                missing_objects = set(objects_in_metadata) - set(objects_in_crate)
                # TODO: undo the unzip bucket upload
                return OperationStatus(False,
                                       f"exception validating objects in ROCrate: Missing {str(missing_objects)} in the crate",
                                       404)
        except Exception as e:
            return OperationStatus(False, f"exception validating objects in ROCrate: {str(e)}", 500)

        # insert the metadata onto the mongo metadata store

        ROCRATE_BUCKET_NAME = minio_config.rocrate_bucket

        data = self.model_dump(by_alias=True)
        data["distribution"] = {"extractedROCrateBucket": ROCRATE_BUCKET_NAME,
                                "archivedROCrateBucket": MINIO_BUCKET,
                                "extractedObjectPath": object_paths_in_crate,
                                "archivedObjectPath": f"{archived_object_path}.zip"
                                }

        insert_op = rocrate_collection.insert_one(data)

        return OperationStatus(True, "", 200)


def UploadZippedCrate(MinioClient, ZippedObject, BucketName, TransactionFolder) -> str:

    source_filepath = Path(ZippedObject.filename).name
    upload_filepath = Path(TransactionFolder) / source_filepath
    
    upload_result = MinioClient.put_object(
        BucketName, 
        str(upload_filepath), 
        ZippedObject.file, 
        #len(ZippedObject.file)
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
        TransactionFolder) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file
        ROCrateBucketName (str): Name of S3 Bucket to upload zip archive of ROCrate

    Returns:
        OperationStatus: Message
    """
 
    try:        
        with open(ZippedObject, "rb") as zip_object:
            zip_contents = zip_object.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:
                for file_info in zip_file.infolist():
                    file_contents = zip_file.read(file_info.filename)

                    # taking the name only  
                    #source_filepath = Path(file_info.filename).name

                    # TODO the source filepath will not start at the root of the rocrate
                    # but rather the full passed filename
                    source_filepath = Path(file_info.filename)
                    upload_filepath = Path(TransactionFolder) / source_filepath

                    MinioClient.put_object(
                        BucketName, 
                        str(upload_filepath), 
                        io.BytesIO(file_contents), 
                        len(file_contents)
                        )                

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
        # zip_contents = Object.read()
        with zipfile.ZipFile(Object, "r") as zip_file:
            for file_info in zip_file.infolist():
                # print(file_info.filename)
                MinioClient.remove_object(MINIO_ROCRATE_BUCKET, file_info.filename)

    except Exception as e:
        return OperationStatus(False, f"Exception removing ROCrate: {str(e)}", 404)

    return OperationStatus(True, "", 200)


def get_metadata_from_crate(minio_client, crate_file_name, Object):
    """Extract metadata from the unzipped ROCrate onto MinIO

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file
        crate_file_name (str): File name to look for

    Returns:
        _type_: content from the crate_file_name
    """

    # Retrieve name of rocrate root directory
    rocrate_root_dir = ''
    try:
        with zipfile.ZipFile(Object) as archive:
            if archive.namelist():
                # convert into a string from Path instance
                rocrate_root_dir = Path(archive.namelist()[0]).parent.joinpath('')
                print("rocrate root dir:", f"{rocrate_root_dir}")
    except zipfile.BadZipFile as zipfile_exception:
        raise Exception(
            message=f"ROCRATE ERROR: exception reading zipfile {zipfile_exception}"
            )

    # List all objects in the bucket
    objects = minio_client.list_objects(
        MINIO_ROCRATE_BUCKET, 
        prefix=f"{rocrate_root_dir}", 
        recursive=True
        )

    for obj in objects:
        if crate_file_name in obj.object_name:
            metadata_content = minio_client.get_object(
                MINIO_ROCRATE_BUCKET, 
                obj.object_name
                ).read()
            return metadata_content

    raise Exception(message="ROCRATE ERROR: ro-crate-metadata.json not found")


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

