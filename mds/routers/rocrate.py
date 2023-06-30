from typing import Union
from fastapi import APIRouter, UploadFile, Form, File, Response, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION, MINIO_ROCRATE_BUCKET
from pydantic import ValidationError
from mds.database import minio, mongo
from mds.models.rocrate import ROCrate
from mds.models.rocrate import *
from mds.utilities.funcs import to_str
from mds.utilities.utils import get_file_from_zip
import zipfile
from  builtins import any as b_any

import json

router = APIRouter()


@router.post("/rocrate/upload",
             summary="Uncompress and upload ROCrate to the object store",
             response_description="The transferred rocrate")
def upload(file: UploadFile = File(...)):
    
    mongo_client = mongo.GetConfig()
    minio_client = minio.GetMinioConfig()    
    
    # Upload the unzipped crate
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
    rocrate_metadata = get_metadata_from_crate(minio_client, file.file, RO_CRATE_METADATA_FILE_NAME)
    
    if not rocrate_metadata:
        return JSONResponse(
                    status_code=404,
                    content={"error": f"{RO_CRATE_METADATA_FILE_NAME} not found in ROCrate"}
                )

    crate = ROCrate(**json.loads(rocrate_metadata))
    #print(crate)
    #print(crate.dict(by_alias=True))

    # Compare objects referenced in the metadata file to the objects in the crate 
    validation_status = crate.validate_rocrate_objects(mongo_client, minio_client, file.file)
                    
    if validation_status.success:
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
        remove_status = remove_unzipped_crate(minio_client, 
                            file.file)
        
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
            summary="List all rocrates",
            response_description="Retrieved list of rocrates")
def rocrate_list(response: Response):
    mongo_client = mongo.GetConfig()
    rocrate = list_rocrates(mongo_client)
    mongo_client.close()

    return rocrate





@router.get("/download-zip")
def download_zip():

    # Set content-type header
    headers = {
        "Content-Type": "application/zip",
        "Content-Disposition": "attachment;filename=test rocrate.zip"
    }

    # Return streaming response with header and data
    return StreamingResponse(fake_data_streamer(), headers=headers, media_type="application/zip")




def fake_data_streamer():
    bucket_name = "test"
    zip_file_name = "UVA/B2AI/test_rocrate/test rocrate.zip"
    
    minio_client = minio.GetMinioConfig()
    # Get zip file metadata
    
    
    file_metadata = minio_client.stat_object(bucket_name, zip_file_name)

    # Get zip file data as a stream
    file_stream = minio_client.get_object(bucket_name, zip_file_name).read()
    
    yield file_stream





@router.get("/rocrate/download/ark:{NAAN}/{postfix:path}",
            summary="Download ROCrate",
            response_description="The downloaded rocrate")
def rocrate_download(
    NAAN: str,     
    postfix: str
    ):
    
    rocrate_id = f"ark:{NAAN}/{postfix}"
    #print(rocrate_id)
    
    

    rocrate = ROCrate.construct(guid=rocrate_id)
    #print(rocrate)

    mongo_client = mongo.GetConfig()
    
    # get the connection to the databases
    minio_client = minio.GetMinioConfig()

    #read_status = rocrate.read_metadata(mongo_client)
    bucket_name, object_loc_in_bucket = get_object_info_from_crate(rocrate_id, mongo_client)

    if not bucket_name or not object_loc_in_bucket:
        return JSONResponse(
                status_code=404,
                content={
                    "@id": rocrate.guid,
                    "error": f"Bucket and/or object paths not found"
                })
    print(bucket_name, object_loc_in_bucket)

    return package_as_zip(bucket_name, object_loc_in_bucket, minio_client)




@router.get("/rocrate/download/stream/ark:{NAAN}/{postfix:path}",
            summary="Download ROCrate",
            response_description="The downloaded rocrate")
def rocrate_download_as_stream(
    NAAN: str,     
    postfix: str
    ):
    
    rocrate_id = f"ark:{NAAN}/{postfix}"
    #print(rocrate_id)
    
    

    rocrate = ROCrate.construct(guid=rocrate_id)
    #print(rocrate)

    mongo_client = mongo.GetConfig()
    
    # get the connection to the databases
    minio_client = minio.GetMinioConfig()

    #read_status = rocrate.read_metadata(mongo_client)
    bucket_name, object_loc_in_bucket = get_object_info_from_crate(rocrate_id, mongo_client)

    if not bucket_name or not object_loc_in_bucket:
        return JSONResponse(
                status_code=404,
                content={
                    "@id": rocrate.guid,
                    "error": f"Bucket and/or object paths not found"
                })
    print(bucket_name, object_loc_in_bucket)

    return package_as_zip_without_saving(bucket_name, object_loc_in_bucket, minio_client)













