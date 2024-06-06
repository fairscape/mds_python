from typing import Union
from fastapi import (
    APIRouter, 
    UploadFile, 
    File, 
#    Form, 
#    Response, 
#    Header
)
from fastapi.responses import (
    JSONResponse, 
#    StreamingResponse, 
#    FileResponse
)
from fairscape_mds.config import get_fairscape_config

from fairscape_mds.models.utils import remove_ids
from fairscape_mds.models.rocrate import (
    UploadExtractedCrate,
    UploadZippedCrate,
    DeleteExtractedCrate,
    GetMetadataFromCrate,
    ListROCrates,
    StreamZippedROCrate,
    GetROCrateMetadata,
    PublishROCrateMetadata,
    PublishProvMetadata,
    ROCrate,
    ROCrateDistribution
)

from fairscape_mds.worker import (
    AsyncRegisterROCrate,
    createUploadJob,
    getUploadJob
    )

import logging
import sys

from pydantic import BaseModel, Field
from typing import List, Dict
from uuid import UUID, uuid4
from pathlib import Path

router = APIRouter()

# setup clients to backend
fairscapeConfig = get_fairscape_config()

mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]
asyncCollection = mongoDB[fairscapeConfig.mongo.async_collection]

minioConfig= fairscapeConfig.minio
minioClient = fairscapeConfig.CreateMinioClient()




@router.post(
        "/rocrate/upload-async",
        summary="",
        status_code=202
        )
async def uploadAsync(
    crate: UploadFile,
    ):

    # create a uuid for transaction
    transactionUUID = uuid4()
    transaction_folder = str(transactionUUID)

    # get the zipfile's filename
    zip_filename = str(Path(crate.filename).name)

    # get the zipfile extracted name
    zip_foldername = str(Path(crate.filename).stem)


    # upload the zipped ROCrate 
    zipped_upload_status, zippedPath = UploadZippedCrate(
        MinioClient=minioClient,
        ZippedObject=crate.file,
        BucketName=fairscapeConfig.minio.rocrate_bucket,
        BucketRootPath=fairscapeConfig.minio.rocrate_bucket_path,
        TransactionFolder=transaction_folder,
        Filename=zip_filename
    )

    if zipped_upload_status is None:
        return JSONResponse(
            status_code=zipped_upload_status.status_code,
            content={
                "error": zipped_upload_status.message
                }
        )

    if fairscapeConfig.minio.rocrate_bucket == '/':
        zippedFilepath = Path(transaction_folder) / Path(zip_filename)
    else:
        zippedFilepath = Path(fairscapeConfig.minio.rocrate_bucket_path) / Path(transaction_folder) / Path(zip_filename)

    # add to the dictionary of tasks
    uploadTask = AsyncRegisterROCrate.apply_async(args=(
        str(transactionUUID),
        str(zippedFilepath)
        ))

    # create the
    uploadJob = createUploadJob(
        str(transactionUUID), 
        str(zippedFilepath)
        )

    uploadMetadata = uploadJob.model_dump()
    uploadMetadata['timeStarted'] = uploadMetadata['timeStarted'].timestamp()

    return JSONResponse(
        status_code=201,
        content=uploadMetadata
        )


@router.get(
        "/rocrate/upload-async/status/{submissionUUID}",
        summary=""
        ) 
def getROCrateStatus(submissionUUID: str):

    jobMetadata = getUploadJob(submissionUUID)

    if jobMetadata is None:
        return JSONResponse(
                status_code = 404,
                content={
                    "submissionUUID": str(submissionUUID), 
                    "error": "rocrate submission not found"
                    }
                )

    else:
        jobResponse = jobMetadata.model_dump()
        jobResponse['timeStarted'] = jobResponse['timeStarted'].timestamp()
        if jobResponse['timeFinished']:
            jobResponse['timeFinished'] = jobResponse['timeFinished'].timestamp()
        
        return JSONResponse(
                status_code=200,
                content=jobResponse
                )


@router.post("/rocrate/upload",
             summary="Unzip the ROCrate and upload to object store",
             response_description="The transferred rocrate")
def rocrate_upload(file: UploadFile = File(...)):

    # create a uuid for transaction
    transaction_folder = str(uuid4())

    # get the zipfile's filename
    zip_filename = str(Path(file.filename).name)

    # get the zipfile extracted name
    zip_foldername = str(Path(file.filename).stem)



    # upload the zipped ROCrate 
    zipped_upload_status, zippedPath = UploadZippedCrate(
        MinioClient=minioClient,
        ZippedObject=file.file,
        BucketName=fairscapeConfig.minio.rocrate_bucket,
        BucketRootPath=fairscapeConfig.minio.rocrate_bucket_path,
        TransactionFolder=transaction_folder,
        Filename=zip_filename
    )

    if zipped_upload_status is None:
        return JSONResponse(
            status_code=zipped_upload_status.status_code,
            content={
                "error": zipped_upload_status.message
                }
        )

    # try to seek the begining of the file
    file.file.seek(0)

    # upload the unziped ROcrate
    extracted_upload_status, extractedPaths = UploadExtractedCrate(
        MinioClient=minioClient,
        ZippedObject=file.file,
        BucketName=fairscapeConfig.minio.default_bucket,
        TransactionFolder=transaction_folder,
    )

    crateDistribution = ROCrateDistribution(
        extractedROCrateBucket = fairscapeConfig.minio.default_bucket,
        archivedROCrateBucket = fairscapeConfig.minio.rocrate_bucket,
        extractedObjectPath = extractedPaths,
        archivedObjectPath =  str(zippedPath)
        )

    if not extracted_upload_status.success:
        return JSONResponse(
            status_code = extracted_upload_status.status_code,
            content = {
                "message": "Error UploadExtractedCrate",
                "error": extracted_upload_status.message
                }
        )


    try:
        # TODO Clean up how distribution is passed around
        # Get metadata from the unzipped crate
        crate = GetMetadataFromCrate(
            MinioClient=minioClient, 
            BucketName=fairscapeConfig.minio.default_bucket,
            TransactionFolder=transaction_folder,
            CratePath=zip_foldername, 
            Distribution = crateDistribution
            )

        if crate is None:
            return JSONResponse(
                status_code=400,
                content={"error": "ROCrate Parsing Error"}
        )

    # TODO handle exception more specifically
    except Exception: 
        return JSONResponse(
            status_code=400,
            content={
                "error": "ro-crate-metadata.json not found in ROCrate"
                }
        )

        
    # TODO check if new identifiers must be minted

    # run entailment
    #crate.entailment()
    

    # turn off validation for not found metadata
    # Compare objects referenced in the metadata file to the objects in the crate 
    #validation_status = crate.validateObjectReference(
    #    MinioClient=minio_client,
    #    MinioConfig=minio_config,
    #    TransactionFolder=transaction_folder,
    #    CrateName=zip_foldername
    #    )


    #if validation_status.success:
        # mint all identifiers in identifier namespace
    
    prov_metadata = PublishProvMetadata(crate, identifierCollection)

    # TODO check mongo write success
    if not prov_metadata:
        pass

    rocrate_metadata = PublishROCrateMetadata(crate, rocrateCollection)

    # TODO check mongo write success
    if not rocrate_metadata:
        pass

    return JSONResponse(
        status_code=201,
        content={
            "created": {
                #"@id": crate.guid,
                "@id": crate.get("@id"),
                "@type": "Dataset",
                #"name": crate.name
                "name": crate.get("name")
            }
        }
    )

    # else:

    #     remove_status = DeleteExtractedCrate(
    #         MinioClient=minio_client, 
    #         BucketName=minio_config.default_bucket,
    #         TransactionFolder=transaction_folder,
    #         CratePath=zip_foldername
    #         )
        
    #     # TODO cleanup operations

    #     if not remove_status.success:
    #         return JSONResponse(
    #             status_code=remove_status.status_code,
    #             content={"error": remove_status.message}
    #         )

    #     return JSONResponse(
    #         status_code=validation_status.status_code,
    #         content={"error": validation_status.message}
    #     )


@router.get("/rocrate",
            summary="List all ROCrates",
            response_description="Retrieved list of ROCrates")
def rocrate_list():
    # TODO check headers to return json or html view

    rocrate = ListROCrates(rocrate_collection)

    # if headers.requests == "text/html":
    #    return Response(
    #       template = "./static/templates/rocrate-list.html" 
    #        content = rocrate_list
    #       )

    return JSONResponse(
        status_code=200,
        content=rocrate
    )

@router.get("/rocrate/ark:{NAAN}/{postfix}",
            summary="Retrieve metadata about a ROCrate",
            response_description="JSON metadata describing the ROCrate")
def dataset_get(NAAN: str, postfix: str):
    """
    Retrieves a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    rocrate_id = f"ark:{NAAN}/{postfix}"

    crate = ROCrate.model_construct(guid=rocrate_id)
    read_status = crate.read(rocrate_collection)

    if read_status.success:
        crate_dict = crate.dict(by_alias=True)
        crate_dict = remove_ids(crate_dict)
        return crate_dict
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )

#@router.get("/rocrate/extracted/download/ark:{NAAN}/{postfix:path}",
#            summary="Download extracted form of ROCrate using StreamingResponse",
#            response_description="ROCrate downloaded as a zip file")
#def extracted_rocrate_download(NAAN: str, postfix: str):
#    rocrate_id = f"ark:{NAAN}/{postfix}"
#    rocrate_metadata = GetROCrateMetadata(rocrate_collection, rocrate_id)
#    if rocrate_metadata is None:
#        return JSONResponse(
#            status_code=404,
#            content={"error": f"unable to find record for RO-Crate: {rocrate_id}"}
#        )
#
#    else:
#        return 


@router.get("/rocrate/archived/download/ark:{NAAN}/{postfix:path}",
            summary="Download archived form of ROCrate using StreamingResponse",
            response_description="ROCrate downloaded as a zip file")
def archived_rocrate_download(
        NAAN: str,
        postfix: str
):
    rocrate_id = f"ark:{NAAN}/{postfix}"
    rocrate_metadata = GetROCrateMetadata(rocrate_collection, rocrate_id)

    if rocrate_metadata is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"unable to find record for RO-Crate: {rocrate_id}"}
        )
        
    else:

        if isinstance(rocrate_metadata.distribution, BaseModel):
            object_path = rocrate_metadata.distribution.archivedObjectPath
        elif isinstance(rocrate_metadata.distribution, dict):
            # Access as a dictionary
            object_path = rocrate_metadata.distribution.get('archivedObjectPath', None)
        return StreamZippedROCrate(
            MinioClient=minio_client,
            BucketName=minio_config.rocrate_bucket,
            ObjectPath = object_path
        )
