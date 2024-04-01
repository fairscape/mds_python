from fastapi import APIRouter, Response, UploadFile, Form, File
from fastapi.responses import JSONResponse, StreamingResponse

import json
from fairscape_mds.mds.config import (
    get_mongo_config,
    get_mongo_client,
    get_minio_config,
    get_minio_client,
    MongoConfig,
    )
from fairscape_mds.mds.models.dataset import Dataset
from fairscape_mds.mds.models.download import Download

router = APIRouter()


@router.post("/download")
async def data_download_create_metadata(download: Download):
    """
	create metadata record for a file	
	"""

    mongo_client = get_mongo_client()

    # create metadata record for data download
    create_metadata_status = download.create_metadata(mongo_client)

    if create_metadata_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": download.guid,
                    "@type": "DataDownload",
                    "name": download.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=create_metadata_status.status_code,
            content={"error": create_metadata_status.message}
        )


@router.post("/register")
def register_download(download = Form(...), file: UploadFile = File(...)):

    # parse the download string from the 
    dl = Download(**json.loads(download))


    mongo_client = get_mongo_client()
    minio_client = get_minio_client()


    registration_status = dl.register(
        mongo_client, 
        minio_client, 
        file.file
        )

    mongo_client.close()

    if registration_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": dl.guid,
                    "@type": "Download",
                    "name": dl.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=registration_status.status_code,
            content={"error": registration_status.message}
        )


@router.post("/datadownload/ark:{NAAN}/{download_id}/upload")
async def data_download_upload(NAAN: str, download_id: str, file: UploadFile):
    data_download = Download.model_construct(id=f"ark:{NAAN}/{download_id}")

    minio_client = get_minio_client()
    mongo_client = get_mongo_client()

    upload_status = data_download.create_upload(
        Object=file,
        MongoClient=mongo_client,
        MinioClient=minio_client
    )

    if upload_status.success:
        return JSONResponse(
            status_code=201,
            content={"updated": {"@id": data_download.guid, "@type": "DataDownload", "name": data_download.name}}
        )
    else:
        return JSONResponse(
            status_code=upload_status.status_code,
            content={"error": upload_status.message}
        )


@router.get("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_read(NAAN: str, download_id: str):
    """
	read the data download metadata 

	To resolve the metadata
	GET /datadownload/ark:99999/ex-upload

	To resolve to the file	
	GET /datadownload/ark:99999/ex-upload/download
	"""

    data_download_id = f"ark:{NAAN}/{download_id}"
    data_download = Download.model_construct(guid=data_download_id)

    # get the connection to the databases
    mongo_client = get_mongo_client()
    read_status = data_download.read_metadata(mongo_client)

    # if the metadata wasn't found successfully handle errors
    if read_status.success != True:

        if read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": data_download.guid,
                    "error": "data download not found"
                })

        else:
            return JSONResponse(
                status_code=read_status.status_code,
                content={
                    "@id": data_download.guid,
                    "error": read_status.message
                })

    # if the metadata is requested return the metadata
    return JSONResponse(
        status_code=200,
        content=data_download.json(by_alias=True)
    )


@router.get("/datadownload/ark:{NAAN}/{download_id}/download")
async def data_download_read(NAAN: str, download_id: str):
    data_download_id = f"ark:{NAAN}/{download_id}"
    data_download = Download.model_construct(guid=data_download_id)

    # get the connection to the databases
    mongo_client = get_mongo_client()
    minio_client = get_minio_client()

    read_status = data_download.read_metadata(mongo_client)

    if read_status.success != True:

        if read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": data_download.guid,
                    "error": "data download not found"
                })

        else:
            return JSONResponse(
                status_code=read_status.status_code,
                content={
                    "@id": data_download.guid,
                    "error": read_status.message
                })

    # get the upload file from minio and stream it back to the user
    return StreamingResponse(data_download.read_object(minio_client), media_type="application/octet-stream")


@router.delete("/datadownload/ark:{NAAN}/{download_id}")
async def transfer_delete(NAAN: str, download_id: str):
    """
	delete the data download, removing its content inside minio but leaving a record in mongo
	"""
    minio_client = get_minio_client()
    mongo_client = get_mongo_client()

    data_download = Download.model_construct(id=f"ark:{NAAN}/{download_id}")
    delete_status = data_download.delete(mongo_client, minio_client)

    if delete_status.success != True:
        return JSONResponse(
            content={
                "@id": data_download.guid,
                "error": delete_status.message
            },
            status_code=delete_status.status_code
        )

    return JSONResponse(
        status_code=200,
        content={
            "deleted": {
                "@id": data_download.guid,
                "@type": "DataDownload",
                "name": data_download.name
            }
        }
    )


@router.put("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_update(NAAN: str, download_id: str, data_download: Download):
    mongo_client = get_mongo_client()

    data_download.id = f"ark:{NAAN}/{download_id}"
    update_status = data_download.update(mongo_client)

    if update_status.success != True:
        return JSONResponse(
            status_code=update_status.status_code,
            content={
                "@id": data_download.guid,
                "error": update_status.message
            })

    return JSONResponse(
        status_code=200,
        content={
            "updated": {
                "@id": data_download.guid,
                "@type": "DataDownload",
                "name": data_download.name
            }
        })
