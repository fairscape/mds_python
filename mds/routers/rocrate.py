from typing import Union
from fastapi import APIRouter, UploadFile, Form, File, Response, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION, MINIO_ROCRATE_BUCKET
from pydantic import ValidationError
from mds.database import minio, mongo
from mds.models.rocrate import ROCrate
from mds.models.rocrate import uncompress_upload_rocrate, get_metadata_from_crate, list_rocrates, read_rocrate_metadata
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
    
    upload_status = uncompress_upload_rocrate(         
        minio_client, 
        file.file
    )

    
    RO_CRATE_METADATA_FILE_NAME = 'ro-crate-metadata.json'
    
    rocrate_metadata = get_metadata_from_crate(minio_client, file.file, RO_CRATE_METADATA_FILE_NAME)
    # print(rocrate_metadata)
    if not rocrate_metadata:
        return JSONResponse(
                    status_code=500,
                    content={"error": f"{RO_CRATE_METADATA_FILE_NAME} not found in ROCrate"}
                )

    crate = ROCrate(**json.loads(rocrate_metadata))
    #print(crate)
    #print(crate.dict(by_alias=True))

    crate.validate_rocrate_objects(mongo_client, minio_client, file.file)
                    
                


    if upload_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": "crate.guid",
                    "@type": "Dataset",
                    "name": "crate.name"
                }
            }
        )
    else:
        return JSONResponse(
            status_code=upload_status.status_code,
            content={"error": upload_status.message}
        )
    


@router.get("/rocrate",
            summary="List all rocrates",
            response_description="Retrieved list of rocrates")
def rocrate_list(response: Response):
    mongo_client = mongo.GetConfig()
    rocrate = list_rocrates(mongo_client)
    mongo_client.close()

    return rocrate


@router.get("/rocrate/download/ark:{NAAN}/{org}/{proj}/{postfix}",
            summary="Download ROCrate",
            response_description="The downloaded rocrate")
def rocrate_download(
    NAAN: str, 
    org: str, 
    proj: str,
    postfix: str
    #Authorization: Union[str, None] = Header(default=None)
    ):
    
    rocrate_id = f"ark:{NAAN}/{org}/{proj}/{postfix}"
    
    

    rocrate = ROCrate.construct(guid=rocrate_id)
    print(rocrate)

    mongo_client = mongo.GetConfig()
    
    # get the connection to the databases
    minio_client = minio.GetMinioConfig()

    #read_status = rocrate.read(mongo_client)

    projection={'_id': False}
    
    

    try:        
        crate_metadata = read_rocrate_metadata(mongo_client, rocrate.guid)
        print(crate_metadata)
        if isinstance(crate_metadata, str):
            print("str")
        if isinstance(crate_metadata, dict):
            print("dict")
        for k, value in crate_metadata.items():
                    #print("\nkey :", k, "value :", value)
                    #setattr(self, k, value)
                    if k == "distribution":
                        print(value)
                        convert_dist = json.dumps(value)
                        dist = json.loads(convert_dist)
                        #print(dist[0]['uncompressedRocrateBucket'])
                        bucket = dist[0]['compressedRocrateBucket']
                        #print(dist[0]['uncompressed_ObjectPaths'])
                        obj_path = dist[0]['compressedObjectPath']

                        if not bucket or obj_path:
                            return JSONResponse(
                                status_code=404,
                                content={
                                    "@id": rocrate.guid,
                                    "error": "rocrate not found"
                            })

                        with minio_client.get_object(bucket, obj_path) as minio_object:
                            return StreamingResponse(minio_object,
                                                     media_type="application/x-zip-compressed", 
                                                     headers = { "Content-Disposition": f"attachment; filename=rocrate.zip"})
    except Exception as e:
        #return {"message": e.messaage}
        return JSONResponse(
                status_code=404,
                content={
                    "@id": rocrate.guid,
                    "error": "rocrate not found"
                })


    #crate_model = crate_metadata

    """ if read_status.success != True:

        if read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": rocrate.guid,
                    "error": "rocrate not found"
                })

        else:
            return JSONResponse(
                status_code=read_status.status_code,
                content={
                    "@id": rocrate.guid,
                    "error": read_status.message
                })
 """
    # get the upload file from minio and stream it back to the user
    #return StreamingResponse(rocrate.read_object(minio_client), media_type="application/octet-stream")
    
    
    

    
    """ download_status = rocrate.download_crate(mongo_client)
    mongo_client.close()

    if download_status.success:
        return rocrate
    else:
        return JSONResponse(
            status_code=download_status.status_code,
            content={"error": download_status.message}
            )
 """






























