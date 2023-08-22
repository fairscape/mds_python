from typing import Union
from fastapi import APIRouter, UploadFile, Form, File, Response, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from mds.config import (
    get_minio_config,
    get_minio_client,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
)

from mds.database import minio, mongo



from mds.models.rocrate import *
from mds.utilities.funcs import to_str
from mds.utilities.utils import get_file_from_zip
from  builtins import any as b_any

import json

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
    # Unzip the ROCrate and upload to MinIO
    upload_status = unzip_and_upload(
        minio_client,
        file.file
    )

    if not upload_status.success:
        return JSONResponse(
            status_code=upload_status.status_code,
            content={"error": upload_status.message}
        )

    RO_CRATE_METADATA_FILE_NAME = 'ro-crate-metadata.json'

    # Get metadata from the unzipped crate
    rocrate_metadata = get_metadata_from_crate(
        minio_client, 
        RO_CRATE_METADATA_FILE_NAME
        )
    
    if not rocrate_metadata:

        return JSONResponse(
            status_code=404,
            content={"error": f"{RO_CRATE_METADATA_FILE_NAME} not found in ROCrate"}
        )

    # TODO handle validation failures gracefully
    #try:

    #except ValidationError as e:
        # try to parse differently
        # additionalType generation
    #    pass
        
    crate = ROCrate(**json.loads(rocrate_metadata))

    # TODO check if new identifiers must be minted


    # run entailment
    crate.entailment()

    

    # Compare objects referenced in the metadata file to the objects in the crate 
    validation_status = crate.validate_rocrate_objects(mongo_client, minio_client, file.file)


    if validation_status.success:


        # mint rocrate identifier
        # TODO check mongo write success
        insert_rocrate = PublishROCrateMetadata(crate, rocrate_collection)

        # mint all identifiers in identifier namespace
        # TODO check mongo write success
        insert_identifiers = PublishProvMetadata(crate, identifier_collection)

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

        remove_status = remove_unzipped_crate(
            minio_client, 
            rocrate.file
            )
        

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
def rocrate_list(response: Response):
    rocrate = list_rocrates(mongo_client)
    mongo_client.close()
    return rocrate


@router.get("/rocrate/extracted/download/ark:{NAAN}/{postfix:path}",
            summary="Download extracted form of ROCrate using StreamingResponse",
            response_description="ROCrate downloaded as a zip file")
def extracted_rocrate_download(NAAN: str, postfix: str):

    rocrate_id = f"ark:{NAAN}/{postfix}"

    rocrate_metadata = get_metadata_by_id(rocrate_collection, rocrate_id)
    if rocrate_metadata:
        bucket_name = ''
        object_name = ''
        for key, value in rocrate_metadata.items():
            if key == 'distribution':
                if value['extractedROCrateBucket']:
                    bucket_name = value['extractedROCrateBucket']
                if value['extractedObjectPath']:
                    object_name = value['extractedObjectPath']
                    break

        if not bucket_name or not object_name:
            return JSONResponse(
                status_code=404,
                content={"error": f"unable to find the object and bucket for RO-Crate: {rocrate_id}"}
            )
        else:
            return zip_extracted_rocrate(bucket_name, object_name, minio_client)

    else:
        return JSONResponse(
            status_code=404,
            content={"error": f"unable to find record for RO-Crate: {rocrate_id}"}
        )


@router.get("/rocrate/archived/download/ark:{NAAN}/{postfix:path}",
            summary="Download archived form of ROCrate using StreamingResponse",
            response_description="ROCrate downloaded as a zip file")
def archived_rocrate_download(
        NAAN: str,
        postfix: str
):
    rocrate_id = f"ark:{NAAN}/{postfix}"
    rocrate_metadata = get_metadata_by_id(rocrate_collection, rocrate_id)

    if rocrate_metadata:
        bucket_name = ''
        object_name = ''
        for key, value in rocrate_metadata.items():
            if key == 'distribution':
                if value['archivedROCrateBucket']:
                    bucket_name = value['archivedROCrateBucket']
                if value['archivedObjectPath']:
                    object_name = value['archivedObjectPath']
                    break

        if not bucket_name or not object_name:
            return JSONResponse(
                status_code=404,
                content={"error": f"unable to find the object and bucket for RO-Crate: {rocrate_id}"}
            )
        else:
            return zip_archived_rocrate(bucket_name, object_name, minio_client)

    else:
        return JSONResponse(
            status_code=404,
            content={"error": f"unable to find record for RO-Crate: {rocrate_id}"}
        )
