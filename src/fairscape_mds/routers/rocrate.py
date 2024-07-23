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
from fairscape_mds.models.user import UserLDAP
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
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
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
        currentUser,
        str(transactionUUID),
        str(zippedFilepath)
        ))

    # create the
    uploadJob = createUploadJob(
        uploadUser=currentUser.dn,
        transactionFolder=str(transactionUUID), 
        zippedCratePath=str(zippedFilepath)
        )

    uploadMetadata = uploadJob.model_dump()
    uploadMetadata['timeStarted'] = uploadMetadata['timeStarted'].timestamp()

    return JSONResponse(
        status_code=201,
        content=uploadMetadata
        )


@router.get(
        "/rocrate/upload/status/{submissionUUID}",
        summary="Check the Status of an Asynchronous Upload Job"
        ) 
def getROCrateStatus(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    submissionUUID: str
    ):

    jobMetadata = getUploadJob(submissionUUID)

    # check authorization to view upload status
    if currentUser.dn != jobMetadata.uploadUser:
        return JSONResponse(
                status_code = 401,
                content={
                    "submissionUUID": str(submissionUUID), 
                    "error": "User Unauthorized to View Upload Job"
                    }
                )
        

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
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    ):

    if fairscapeConfig.ldap.adminDN in currentUser.memberOf:
        cursor = rocrateCollection.find(
            {},
            projection={ 
                "_id": 0, 
            }
        )

    else:
        # filter by group ownership
        cursor = rocrateCollection.find(
            {"permissions.group": currentUser.memberOf[0]} , 
            projection={ "_id": 0}
            )

    responseJSON = { 
        "rocrates": [
            {
                "@id": f"{fairscapeConfig.url}/{crate.get('@id')}",
                "name": crate.get("name"),
                "description": crate.get("description"),
                "keywords": crate.get("keywords"),
                "sourceOrganization": crate.get("sourceOrganization"),
                "contentURL": f"{fairscapeConfig.url}/rocrate/download/{crate.get('@id')}",
                "@graph": [
                    {
                        "@id": f"{fairscapeConfig.url}/{crateElem.get("@id")}",
                        "@type": crateElem.get("@type"),
                        "name": crateElem.get("name"),
                        "contentURL": f"{fairscapeConfig.url}/dataset/download/{crateElem.get('@id')}"
                     }
                     for crateElem in crate.get("@graph")
                ]
            } for crate in list(cursor)
        ]
    }
    
    return JSONResponse(
        status_code=200,
        content=responseJSON
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

    rocrateGUID = f"ark:{NAAN}/{postfix}"
    rocrateMetadata = rocrateCollection.find_one({"@id": rocrate_id}, projection={"_id":0}) 

    if rocrateMetadata is None:
        return JSONResponse(
            status_code=404,
            content={"@id": rocrateGUID, "error": "ROCrate not found"}
        )


    # format json-ld with absolute URIs
    rocrateMetadata['@id'] = f"{fairscapeConfig.url}/{rocrateGUID}"

    for crateElem in rocrateMetadata.get("@graph", []):
        crateElem['@id'] = f"{fairscapeConfig.url}/{crateElem['@id']}"

    return rocrateMetadata
    


@router.get("/rocrate/download/ark:{NAAN}/{postfix}",
            summary="Download archived form of ROCrate using StreamingResponse",
            response_description="ROCrate downloaded as a zip file")
def archived_rocrate_download(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str,
    postfix: str
    ): 
    """
    Download the Zipped ROCrate from MINIO
    """

    rocrateGUID = f"ark:{NAAN}/{postfix}"
    rocrateMetadata = rocrateCollection.find_one(
        {"@id": rocrateGUID}, 
        projection={"distribution": 1}
        )
    
    if rocrateMetadata is None:
        return JSONResponse(
            status_code=404,
            content={
                "@id": f"{fairscapeConfig.url}/{rocrateGUID}",
                "error": f"unable to find record for RO-Crate: {rocrate_id}"
            }
        )

    # AuthZ: check if user is allowed to download 
    # if a user is a part of the group that uploaded the ROCrate OR user is an Admin
    if rocrate_metadata.permission.group in currentUser.memberOf or fairscapeConfig.ldap.adminDN in currentUser.memberOf:
        objectPath = rocrateMetadata.get("archivedObjectPath", None)
        return StreamZippedROCrate(
            MinioClient=minio_client,
            BucketName=minio_config.rocrate_bucket,
            ObjectPath = object_path
        )

    else:
        # return a 401 error
        return JSONResponse(
            status_code=401,
            content={
            "@id": f"{fairscapeConfig.url}/{rocrateGUID}",
            "error": "Current user is not authorized to download ROcrate"
            }
        )
        
