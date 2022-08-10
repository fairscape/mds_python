from fastapi import APIRouter, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from mds.database import mongo, minio
from mds.models.dataset import Dataset
from mds.models.download import Download as DataDownload
from mds.models.compact.user import UserCompactView

router = APIRouter()


@router.post("/datadownload")
async def data_download_create_metadata(data_download: DataDownload):
    """
	create metadata record for a file	
	"""

    mongo_client = mongo.GetConfig()

    # TODO check that dataset is set
    # dataset_id = f"ark:{NAAN}/{dataset_id}"
    # data_download.encodesCreativeWork.id = dataset_id

    # create metadata record for data download
    create_metadata_status = data_download.create_metadata(mongo_client)

    if create_metadata_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": data_download.id,
                    "@type": "DataDownload",
                    "name": data_download.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=create_metadata_status.status_code,
            content={"error": create_metadata_status.message}
        )


@router.post("/register")
async def register_download():
    pass

@router.post("/datadownload/ark:{NAAN}/{download_id}/upload")
async def data_download_upload(NAAN: str, download_id: str, file: UploadFile):
    data_download = DataDownload.construct(id=f"ark:{NAAN}/{download_id}")

    minio_client = minio.GetMinioConfig()
    mongo_client = mongo.GetConfig()

    upload_status = data_download.create_upload(
        Object=file,
        MongoClient=mongo_client,
        MinioClient=minio_client
    )

    if upload_status.success:
        return JSONResponse(
            status_code=201,
            content={"updated": {"@id": data_download.id, "@type": "DataDownload", "name": data_download.name}}
        )
    else:
        return JSONResponse(
            status_code=upload_status.status_code,
            content={"error": upload_status.message}
        )


@router.get("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_read(NAAN: str, download_id: str):
    """
	read the data download object

	To resolve the metadata
	GET /datadownload/ark:99999/ex-upload

	To resolve to the file	
	GET /datadownload/ark:99999/ex-upload?object=1
	"""

    data_download_id = f"ark:{NAAN}/{download_id}"
    data_download = DataDownload.construct(id=data_download_id)

    # get the connection to the databases
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    minio_client = minio.GetMinioConfig()

    read_status = data_download.read_metadata(mongo_collection)

    # if the metadata wasn't found successfully handle errors
    if read_status.success != True:

        if read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": data_download.id,
                    "error": "data download not found"
                })

        else:
            return JSONResponse(
                status_code=read_status.status_code,
                content={
                    "@id": data_download.id,
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
    data_download = DataDownload.construct(id=data_download_id)

    # get the connection to the databases
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    minio_client = minio.GetMinioConfig()

    read_status = data_download.read_metadata(mongo_collection)

    if read_status.success != True:

        if read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": data_download.id,
                    "error": "data download not found"
                })

        else:
            return JSONResponse(
                status_code=read_status.status_code,
                content={
                    "@id": data_download.id,
                    "error": read_status.message
                })

    # get the upload file from minio and stream it back to the user
    return StreamingResponse(data_download.read_object(minio_client), media_type="application/octet-stream")


@router.delete("/datadownload/ark:{NAAN}/{download_id}")
async def transfer_delete(NAAN: str, download_id: str):
    """
	delete the data download, removing its content inside minio but leaving a record in mongo
	"""
    minio_client = minio.GetMinioConfig()
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    data_download = DataDownload.construct(id=f"ark:{NAAN}/{download_id}")
    delete_status = data_download.delete(mongo_collection, minio_client)

    if delete_status.success != True:
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
                "@id": data_download.id,
                "@type": "DataDownload",
                "name": data_download.name
            }
        }
    )


@router.put("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_update(NAAN: str, download_id: str, data_download: DataDownload):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    data_download.id = f"ark:{NAAN}/{download_id}"
    update_status = data_download.update(mongo_collection)

    if update_status.success != True:
        return JSONResponse(
            status_code=update_status.status_code,
            content={
                "@id": data_download.id,
                "error": update_status.message
            })

    return JSONResponse(
        status_code=200,
        content={
            "updated": {
                "@id": data_download.id,
                "@type": "DataDownload",
                "name": data_download.name
            }
        })
