from fastapi import APIRouter, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from mds.database import mongo, minio
from mds.models.dataset import Dataset
from mds.models.download import DataDownload
from mds.models.compact.user import UserCompactView


router = APIRouter()

@router.post("/dataset/ark:{NAAN}/{dataset_id}/datadownload/ark:{NAAN}/{download_id}/")
async def data_download_create_metadata(NAAN: str, dataset_id: str, download_id: str,  data_download: DataDownload):
	"""
	create metadata record for a file	
	"""

	# create a mongo_collection
	dataset_id = f"ark:{NAAN}/{dataset_id}"
	data_download_id = f"ark:{NAAN}/{download_id}"

	data_download.id = data_download_id
	data_download.encodesCreativeWork.id = dataset_id

	mongo_collection = mongo.GetConfig()

	# create metadata record for data download
	create_metadata_status = data_download.create_metadata(mongo_collection)

	if create_metadata_status.success:
		return JSONResponse(
			status_code= 201, 
			content= {
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
			content= {"error": create_metadata_status.message}
		)


@router.post("/datadownload/ark:{NAAN}/{download_id}/upload")
async def data_download_upload(NAAN: str, download_id: str, upload_file: UploadFile):

	data_download = DataDownload.construct(id= f"ark:{NAAN}/{download_id}")

	mongo_collection = mongo.GetConfig()
	minio_client = minio.GetMinioConfig()


	upload_status = data_download.create_upload(
		Object = upload_file, 
		MongoCollection = mongo_collection, 
		MinioClient = minio_client
		)

	if upload_status.success:
		return JSONResponse(
			status_code=201,
			content= {"uploaded": {"@id": data_download.id, "@type": "DataDownload", "name": data_download.name}}
			)
	else:
		return JSONResponse(
			status_code = upload_status.status_code,
			content = {"error": upload_status.message}
		)


@router.get("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_read(NAAN: str, download_id: str, object: bool=False):
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
	mongo_collection = mongo.GetConfig()
	minio_client = minio.GetMinioConfig()

	read_status = data_download.read_metadata(mongo_collection)

	# if the metadata wasn't found successfully handle errors
	if read_status.success != True:

		if read_status.status_code == 404:
			return JSONResponse(
				status_code= 404, 
				content = {
					"@id": data_download.id, 
					"error": "data download not found"
					})

		else:
			return JSONResponse(
				status_code = read_status.status_code,
				content = {
					"@id": data_download.id,
					"error": read_status.message
				})

	# if the metadata is requested return the metadata
	if object == False:
		return JSONResponse(status_code=200, content=read_status.json(by_alias=True))

	# if the object was requested  
	else:

		# get the upload file from minio and stream it back to the user
		return StreamingResponse(data_download.read_object(minio_client), media_type="application/octet-stream")




@router.delete("/datadownload/ark:{NAAN}/{upload_id}")
async def transfer_delete(NAAN: str, dataset_id: str, upload_id: str):
	"""
	delete the data download, removing its content inside minio but leaving a record in mongo
	"""

	return {"status": "in_progress"}


@router.put("/datadownload/ark:{NAAN}/{download_id}")
async def data_download_update(NAAN:str, download_id: str):

	return {"status": "in_progress"}