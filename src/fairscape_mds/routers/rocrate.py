from typing import Union
from fastapi import (
    APIRouter, 
    Depends,
    UploadFile, 
    File, 
)
from fastapi.responses import JSONResponse

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

from typing import List, Dict
from uuid import UUID, uuid4
from pathlib import Path

from typing import Annotated
from fairscape_mds.models.user import User
from fairscape_mds.auth.oauth import getCurrentUser

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
        summary="Upload a Zipped RO-Crate",
        status_code=202
        )
def uploadAsync(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    crate: UploadFile,
):

    # create a uuid for transaction
    transactionUUID = uuid4()
    transaction_folder = str(transactionUUID)

    # get the zipfile's filename
    zip_filename = str(Path(crate.filename).name)

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

    if not fairscapeConfig.minio.rocrate_bucket_path or fairscapeConfig.minio.rocrate_bucket_path == "/":
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
        summary="Check the Status of an Asynchronous Upload Job"
        ) 
def getROCrateStatus(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    submissionUUID: str
    ):

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


@router.get("/rocrate",
    summary="List all ROCrates",
    response_description="Retrieved list of ROCrates")
def rocrate_list(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    ):

    rocrate = ListROCrates(rocrate_collection)

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


@router.get("/rocrate/download/ark:{NAAN}/{postfix}",
            summary="Download archived form of ROCrate using StreamingResponse",
            response_description="ROCrate downloaded as a zip file")
def archived_rocrate_download(
    currentUser: Annotated[User, Depends(getCurrentUser)],
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
