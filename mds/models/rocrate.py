from fastapi.responses import StreamingResponse

import uuid
import zipfile
import re
import hashlib

from mds.config import get_ark_naan
from pydantic import (
    Field,
    constr,
    BaseModel,
    ValidationError, 
    computed_field
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
from minio.deleteobjects import DeleteObject

from datetime import datetime
import pymongo

from mds.models.fairscape_base import FairscapeBaseModel
from mds.utilities.operation_status import OperationStatus

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
    guid: str = Field(alias="@id")
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
    guid: str = Field(alias="@id")
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
    guid: str = Field(alias="@id")
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
    guid: str = Field(alias="@id")
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


class ROCrateDistribution(BaseModel):
    extractedROCrateBucket: Optional[str] = Field(default=None)
    archivedROCrateBucket: Optional[str] = Field(default=None)
    extractedObjectPath: Optional[List[str]] = Field(default=None)
    archivedObjectPath: Optional[str] = Field(default=None)


class ROCrate(FairscapeBaseModel):
    guid: str = Field(alias="@id")
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
    contentURL: Optional[str] = Field(
        default=None, 
        description="Value for ROCrate S3 URI of zip location"
        )
    distribution: Optional[ROCrateDistribution] = Field(default=None)

    # turning off automatically generated GUIDs
    #@computed_field(alias="@id")
    #@property
    def generate_guid(self) -> str:

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


    def validateObjectReference(
            self, 
            MinioClient,
            MinioConfig,
            TransactionFolder, 
            CrateName,
            ) -> OperationStatus:

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

        rocrate_logger.info(
            "ParsingROCrate message='found files in rocrate metadata'\t" +
            f"transaction={TransactionFolder}\t" +
            f"objects={objects_in_metadata}"
            )

        object_path = f"{TransactionFolder}/{CrateName}"

        try:
            object_instances_in_crate = MinioClient.list_objects(
                bucket_name = MinioConfig.default_bucket, 
                prefix=object_path, 
                recursive=True
                )

            object_paths_in_crate = [
                obj_instance.object_name for obj_instance in object_instances_in_crate
                ]
            objects_in_crate = [
                Path(obj).name for obj in object_paths_in_crate
                ]

            rocrate_logger.info(
                "ParsingROCrate\t" +
                "message='found objects in minio'\t" +
                f"transaction={TransactionFolder}\t" +
                f"objects={objects_in_crate}"
                )

            # Check if metadata objects exist in the crate
            if set(objects_in_metadata).issubset(set(objects_in_crate)):
                # calculate filesize
                # file_size = os.fstat(Object.fileno()).st_size
                # print(file_size)

                rocrate_logger.info(
                    "validateObjectReference\t" +
                    f"transaction_folder={TransactionFolder}\t" +
                    "message='validation successfull'\t" +
                    "success=true"
                )

                # insert the metadata onto the mongo metadata store
                self.distribution = ROCrateDistribution(**{
                    "extractedObjectPath": object_paths_in_crate,
                    "archivedObjectPath": f"{object_path}.zip"
                })

                zip_bucket = MinioConfig.rocrate_bucket
                self.contentURL =  f"s3a://{zip_bucket}/{TransactionFolder}/{CrateName}.zip"

                return OperationStatus(True, "", 200)

            else:
                missing_objects = set(objects_in_metadata) - set(objects_in_crate)

                rocrate_logger.error(
                    "ParsingROCrate\t" +
                    "message='Objects Missing Annotation'\t" +
                    f"transaction={TransactionFolder}\t" +
                    f"objects={missing_objects}"
                    )

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

class ProcessROCrate():
    """ Class for Processing an ROCrate
    """

    def __init__(self, crate_file):
        self.crate_file = crate_file

    def uploadExtractedCrate():
        pass

    def Process(self):
        pass



def UploadZippedCrate(
        MinioClient, 
        ZippedObject, 
        BucketName, 
        TransactionFolder: uuid.UUID, 
        Filename: str,
        ) -> str:

    #source_filepath = Path(ZippedObject.filename).name
    upload_filepath = Path(str(TransactionFolder)) / Path(Filename)
    
    upload_result = MinioClient.put_object(
        bucket_name=BucketName, 
        object_name=str(upload_filepath), 
        data=ZippedObject, 
        length=-1,
        part_size= 5 * 1024 * 1024 ,
        content_type="application/zip"
        )                

    # log upload of zipped rocrate
    rocrate_logger.info(
        "UploadZippedCrate\t" +
        f"transaction={TransactionFolder}\t" +
        "message='Uploaded Zipped Crate Minio'\t" +
        f"object_name='{upload_result.object_name}\t' " +
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
                    "UploadExtractedCrate\t" +
                    f"transaction={TransactionFolder}\t" +
                    "message='Uploaded File to minio' " +
                    f"object_name='{upload_result.object_name}' " +
                    f"object_etag='{upload_result.etag}'"
                    )

    except Exception as e:
        return OperationStatus(False, f"Exception uploading ROCrate: {str(e)}", 500)

    return OperationStatus(True, "", 200)



def DeleteExtractedCrate(
        MinioClient, 
        BucketName: str, 
        TransactionFolder: str,
        CratePath: str
        ) -> OperationStatus:
    """Accepts zipped ROCrate, unzip and upload onto MinIO.

    Args:
        MinioClient (Any): MinIO client
        Object (Any): zipped ROCrate file

    Returns:
        OperationStatus: Message
    """


    try:
        # remove all listed files
        minio_listed_objects = MinioClient.list_objects(
            bucket_name = BucketName, 
            prefix=CratePath, 
            recursive=True
            )

        object_names = [
            obj_instance.object_name for obj_instance in minio_listed_objects
            ]

        delete_list = [DeleteObject(obj) for obj in object_names]
        
        delete_errors = MinioClient.remove_objects(
                bucket_name=BucketName, 
                delete_object_list=delete_list
        )

        # if errors occur
        if len(delete_errors) != 0:

            for error in delete_errors:
                rocrate_logger.error(
                    "DeleteExtractedCrate\t"+
                    f"transaction_folder={TransactionFolder}\t" +
                    f"bucket_name={BucketName}\t" +
                    f"object_names={object}\t" +
                    f"error={str(error)}"
                )

            return OperationStatus(False, f"ERROR Deleting ROCrate: {delete_errors}", 400)
        
        
        rocrate_logger.info(
            "DeleteExtractedCrate\t" +
            f"transaction_folder={TransactionFolder}\t" +
            f"bucket_name={BucketName}\t" +
            f"objects={object_names}\t"
        )

    except Exception as e:
        return OperationStatus(False, f"Exception removing ROCrate: {str(e)}", 404)

    return OperationStatus(True, "", 200)


def GetMetadataFromCrate(MinioClient, BucketName, TransactionFolder, CratePath):
    """Extract metadata from the unzipped ROCrate onto MinIO
    
    Args:
        MinioClient (Any): MinIO client
        BucketName (str): name for bucket to search for the crate metadata
        TransactionFolder (str): UUID for this transaction 
        CratePath (str): name of expanded crate path

    Returns:
        ro_crate_json (dict): contents of the ro-crate-metadata.json file as a dictionary
    """

    rocrate_logger.info(
        "GetMetadataFromCrate\t" +
        f"transaction_folder={TransactionFolder}" +
        f"crate_path={CratePath}" 
    )

    try:
        # List all objects in the bucket
        ro_crate_response = MinioClient.get_object(
            bucket_name= BucketName, 
            object_name=f"{TransactionFolder}/{CratePath}/ro-crate-metadata.json", 
            )

        # read all metadata as json
        ro_crate_json = ro_crate_response.read()

        # parse file contents into dictionary
        try:
            ro_crate_dict = json.loads(ro_crate_json)
        except Exception:
            return None

        # parse dictionary into ROCrate pydantic model
        try:
            crate = ROCrate(**ro_crate_dict)
            return crate
        except ValidationError:

            # TODO try to parse gracefully
            # additionalType generation
            return None

    except Exception as e:
        raise Exception(f"ROCRATE ERROR: ro-crate-metadata.json not found exception={str(e)}")


def ListROCrates(ROCrateCollection: pymongo.collection.Collection):
    """ List all ROCrates uploaded to FAIRSCAPE
    """

    rocrate_cursor = ROCrateCollection.find(
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


def StreamZippedROCrate(MinioClient, BucketName: str, ObjectPath: str):

    headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": "attachment;filename=downloaded-rocrate.zip"
    }

    file_stream = MinioClient.get_object(
        bucket_name=BucketName, 
        object_name=ObjectPath
        ).read()

    return StreamingResponse(
        generator_iterfile(file_stream), 
        headers=headers, 
        media_type="application/zip"
        )


# generator function to iterate over that file-like object
def generator_iterfile(file_stream) -> Generator:
    yield file_stream

def get_data_from_file(file_path: str) -> Generator:
    with open(file=file_path, mode="rb") as file_like:
        yield file_like.read()


def get_data_from_stream(file_data) -> Generator:
    yield file_data.getvalue()



def GetROCrateMetadata(rocrate_collection: pymongo.collection, rocrate_id):
    # ignore _id in mongo documents
    query_projection = {'_id': False}
    # find rocrate metadata by the unique @id
    query = rocrate_collection.find_one(
        {'@id': rocrate_id},
        projection=query_projection
        )
 
    if query:
        try:
            parsed_crate = ROCrate(**query)
            return parsed_crate
        except Exception as e:
            raise Exception(message=f"ROCRATE Metadata not valid: {str(e)}")
    else:
        return None    


def PublishROCrateMetadata(
        rocrate: ROCrate, 
        rocrate_collection: pymongo.collection.Collection
        ) -> bool:  
    """ Insert ROCrate metadata into mongo rocrate collection
    """

    rocrate_json = rocrate.model_dump(by_alias=True)
    insert_result = rocrate_collection.insert_one(rocrate_json)
    if insert_result.inserted_id is None:
        return False
    else:
        return True


def PublishProvMetadata(
        rocrate: ROCrate, 
        identifier_collection: pymongo.collection.Collection
        ) -> bool:
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

