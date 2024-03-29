from typing import Union
from fastapi import (
    APIRouter, 
    UploadFile, 
#    Form, 
    File, 
#    Response, 
#    Header
)
from fastapi.responses import (
    JSONResponse, 
#    StreamingResponse, 
#    FileResponse
)
from mds.config import (
    get_minio_config,
    get_minio_client,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
)
from mds.models.rocrate import (
    UploadExtractedCrate,
    UploadZippedCrate,
    DeleteExtractedCrate,
    GetMetadataFromCrate,
    ListROCrates,
    StreamZippedROCrate,
    GetROCrateMetadata,
    PublishROCrateMetadata,
    PublishProvMetadata
)

import uuid
from pathlib import Path

router = APIRouter()

# setup clients to backend
mongo_config = get_mongo_config()
mongo_client = get_mongo_client()
mongo_db = mongo_client[mongo_config.db]
rocrate_collection = mongo_db[mongo_config.rocrate_collection]
identifier_collection = mongo_db[mongo_config.identifier_collection]
minio_config= get_minio_config()
minio_client = get_minio_client()

casbin_enforcer = get_casbin_enforcer()
casbin_enforcer.load_policy()


@router.post("/rocrate/upload",
             summary="Unzip the ROCrate and upload to object store",
             response_description="The transferred rocrate")
def rocrate_upload(file: UploadFile = File(...)):

    # create a uuid for transaction
    transaction_folder = str(uuid.uuid4())

    # get the zipfile's filename
    zip_filename = str(Path(file.filename).name)

    # get the zipfile extracted name
    zip_foldername = str(Path(file.filename).stem)


    # upload the zipped ROCrate 
    zipped_upload_status = UploadZippedCrate(
        MinioClient=minio_client,
        ZippedObject=file.file,
        BucketName=minio_config.rocrate_bucket,
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
    extracted_upload_status = UploadExtractedCrate(
        MinioClient=minio_client,
        ZippedObject=file.file,
        BucketName=minio_config.default_bucket,
        TransactionFolder=transaction_folder
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
        # Get metadata from the unzipped crate
        crate = GetMetadataFromCrate(
            MinioClient=minio_client, 
            BucketName=minio_config.default_bucket,
            TransactionFolder=transaction_folder,
            CratePath=zip_foldername
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
    crate.entailment()
    

    # Compare objects referenced in the metadata file to the objects in the crate 
    validation_status = crate.validateObjectReference(
        MinioClient=minio_client,
        MinioConfig=minio_config,
        TransactionFolder=transaction_folder,
        CrateName=zip_foldername
        )


    if validation_status.success:

        # mint all identifiers in identifier namespace
        # TODO check mongo write success
        prov_metadata = PublishProvMetadata(crate, identifier_collection)

        if not prov_metadata:
            pass


        rocrate_metadata = PublishROCrateMetadata(crate, rocrate_collection)

        if not rocrate_metadata:
            pass

        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": crate.guid,
                    "@type": "Dataset",
                    "name": crate.name
                }
            }
        )

    else:

        remove_status = DeleteExtractedCrate(
            MinioClient=minio_client, 
            BucketName=minio_config.default_bucket,
            TransactionFolder=transaction_folder,
            CratePath=zip_foldername
            )
        
        # TODO cleanup operations

        if not remove_status.success:
            return JSONResponse(
                status_code=remove_status.status_code,
                content={"error": remove_status.message}
            )

        return JSONResponse(
            status_code=validation_status.status_code,
            content={"error": validation_status.message}
        )


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
        return StreamZippedROCrate(
            MinioClient=minio_client,
            BucketName=minio_config.rocrate_bucket,
            ObjectPath = rocrate_metadata.distribution.archivedObjectPath
        )
