from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from mds.database import mongo
from mds.models.group import Dataset
from mds.models.compact.user import UserCompactView


router = APIRouter()

@router.post("/dataset/ark:{NAAN}/{dataset_id}/upload")
async def transfer_upload(NAAN: str, dataset_id: str):
	return {"status": "in progress"}


@router.get("/dataset/ark:{NAAN}/{dataset_id}/upload/{upload_id}")
async def transfer_download(NAAN: str, dataset_id: str, upload_id: str):
	return {"status": "in progress"}


@router.delete("/dataset/ark:{NAAN}/{dataset_id}/upload/{upload_id}")
async def transfer_delete(NAAN: str, dataset_id: str, upload_id: str):
	return {"status": "in progress"}