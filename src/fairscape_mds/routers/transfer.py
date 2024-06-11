from fastapi import APIRouter, Response, UploadFile, Form, File
from fastapi.responses import JSONResponse, StreamingResponse

import json
from fairscape_mds.config import (
    get_fairscape_config
)
from fairscape_mds.models.dataset import DatasetCreateModel
from fairscape_mds.models.download import (
    DownloadCreateModel,
    DownloadReadModel,
    createDownload,
    getDownloadMetadata,
    getDownloadMinioPath,
    getDownloadContent,
    deleteDownload
)

router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_config = fairscapeConfig.mongo
mongo_client = fairscapeConfig.CreateMongoClient()
mongo_db = mongo_client[mongo_config.db]
identifier_collection = mongo_db[mongo_config.identifier_collection]
user_collection = mongo_db[mongo_config.user_collection]

minioConfig = fairscapeConfig.minio
minioClient = fairscapeConfig.CreateMinioClient()


@router.post("/register")
def register_download(download = Form(...), file: UploadFile = File(...)):

    # parse the download string from the 
    downloadInstance = DownloadCreateModel.model_validate(json.loads(download))

    registrationStatus = createDownload(
            downloadInstance,
            file,
            identifierCollection,
            userCollection,
            )
    
    if registrationStatus.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": downloadInstance.guid,
                    "@type": "Download",
                    "name": downloadInstance.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=registrationStatus.status_code,
            content={"error": registrationStatus.message}
        )



@router.get("/download/ark:{NAAN}/{download_id}")
def data_download_read(NAAN: str, download_id: str):
    """
	read the data download metadata 

	To resolve the metadata
	GET /datadownload/ark:99999/ex-upload

	To resolve to the file	
	GET /datadownload/ark:99999/ex-upload/download
	"""

    downloadGUID = f"ark:{NAAN}/{download_id}"
    
    downloadInstance, readStatus = getDownloadMetadata(downloadGUID, identifierCollection)

    # if the metadata wasn't found successfully handle errors
    if not readStatus.success:

        return JSONResponse(
            status_code=readStatus.status_code,
            content={
                "@id": downloadGUID,
                "error": readStatus.message
            })


    # if the metadata is requested return the metadata
    return JSONResponse(
        status_code=200,
        content=downloadInstance.model_dump_json(by_alias=True)
    )


@router.get("/download/ark:{NAAN}/{download_id}/download")
def data_download_read(NAAN: str, download_id: str):
    downloadGUID = f"ark:{NAAN}/{download_id}"

    minioPath, readStatus = getDownloadMinioPath(
            downloadGUID,
            identifierCollection
            )

    if readStatus.success != True:
        return JSONResponse(
            status_code=readStatus.status_code,
            content={
                "@id": downloadGUID,
                "error": readStatus.message
            })


    # get the upload file from minio and stream it back to the user
    return StreamingResponse(
            getDownloadContent(minioPath, minioClient, minioConfig.default_bucket), 
            media_type="application/octet-stream"
            )


@router.delete("/download/ark:{NAAN}/{download_id}")
def transfer_delete(NAAN: str, download_id: str):
    """
	delete the data download, removing its content inside minio but leaving a record in mongo
	"""
    downloadGUID = f"ark:{NAAN}/{download_id}"

    deleteStatus = deleteDownload(
        downloadGUID,
        identifierCollection,
        userCollection
    )

    if deleteStatus.success != True:
        return JSONResponse(
            content={
                "@id": data_download.id,
                "error": delete_status.message
            },
            status_code=delete_status.status_code
        )

    return JSONResponse(
        status_code=200,
        content={
            "deleted": {
                "@id": downloadGUID,
                "@type": "evi:DataDownload"
            }
        }
    )

