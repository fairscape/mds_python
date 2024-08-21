from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Annotated
from fairscape_mds.models.user import UserLDAP
from fairscape_mds.auth.oauth import getCurrentUser
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.models.publish import APIToken, DataversePublishSettings
from fairscape_mds.models.rocrate import ROCrate
from pathlib import Path
import requests
import json
import io
import zipfile

router = APIRouter()

fairscapeConfig = get_fairscape_config()

minioClient = fairscapeConfig.CreateMinioClient()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
apiTokenCollection = mongoDB['api_tokens']
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]

@router.post("/publish/token")
async def upload_api_token(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    token: str
):
    api_token = APIToken.create(currentUser.cn, token)
    result = apiTokenCollection.update_one(
        {"user_id": currentUser.cn},
        {"$set": api_token.dict()},
        upsert=True
    )
    if result.acknowledged:
        return JSONResponse(status_code=200, content={"message": "API token stored successfully"})
    else:
        raise HTTPException(status_code=500, detail="Failed to store API token")

@router.post("/publish/create/ark:{NAAN}/{postfix}")
async def create_dataset(
    ark: str,
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    settings: DataversePublishSettings
):
    # Retrieve API token
    token_doc = apiTokenCollection.find_one({"user_id": currentUser.cn})
    if not token_doc:
        raise HTTPException(status_code=404, detail="API token not found")
    api_token = APIToken(**token_doc).decrypt_token()

    # Retrieve ROCrate metadata
    rocrate_doc = rocrateCollection.find_one({"@id": ark})
    if not rocrate_doc:
        raise HTTPException(status_code=404, detail="ROCrate not found")
    rocrate = ROCrate(**rocrate_doc)

    # Authorization check
    rocrate_group = rocrate_doc.get("permissions", {}).get("group")
    if rocrate_group not in currentUser.memberOf and fairscapeConfig.ldap.adminDN not in currentUser.memberOf:
        raise HTTPException(status_code=401, detail="User not authorized to publish this ROCrate")

    # Prepare dataset metadata
    metadata = {
        "datasetVersion": {
            "license": {
                "name": "CC0 1.0",
                "uri": "http://creativecommons.org/publicdomain/zero/1.0"
            },
            "metadataBlocks": {
                "citation": {
                    "fields": [
                        {"value": rocrate.name, "typeClass": "primitive", "multiple": False, "typeName": "title"},
                        {
                            "value": [
                                {
                                    "authorName": {"value": author, "typeClass": "primitive", "multiple": False, "typeName": "authorName"},
                                    "authorAffiliation": {"value": "CAMA", "typeClass": "primitive", "multiple": False, "typeName": "authorAffiliation"}
                                } for author in rocrate.author.split(', ')  # Assuming authors are comma-separated
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "author"
                        },
                        {
                            "value": [
                                {
                                    "datasetContactName": {"value": currentUser.cn, "typeClass": "primitive", "multiple": False, "typeName": "datasetContactName"},
                                    "datasetContactEmail": {"value": currentUser.mail, "typeClass": "primitive", "multiple": False, "typeName": "datasetContactEmail"}
                                }
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "datasetContact"
                        },
                        {
                            "value": [
                                {
                                    "dsDescriptionValue": {"value": rocrate.description, "typeClass": "primitive", "multiple": False, "typeName": "dsDescriptionValue"}
                                }
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "dsDescription"
                        },
                        {"value": ["Computer and Information Science"], "typeClass": "controlledVocabulary", "multiple": True, "typeName": "subject"},
                        {
                            "value": [
                                {
                                    "keywordValue": {"value": keyword, "typeClass": "primitive", "multiple": False, "typeName": "keywordValue"}
                                } for keyword in rocrate.keywords
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "keyword"
                        },
                        {"value": "This dataset is part of a ROCrate.", "typeClass": "primitive", "multiple": False, "typeName": "notesText"},
                        {"typeName": "datasetPublicationDate", "multiple": False, "typeClass": "primitive", "value": rocrate.datePublished},
                        {"typeName": "productionDate", "multiple": False, "typeClass": "primitive", "value": rocrate.datePublished}
                    ]
                }
            }
        }
    }

    # Create dataset in Dataverse
    headers = {
        "X-Dataverse-key": api_token,
        "Content-Type": "application/json"
    }
    url = f"{settings.base_url}/api/dataverses/{settings.dataverse_id}/datasets"
    response = requests.post(url, headers=headers, json=metadata)

    if response.status_code == 201:
        dataset_info = response.json()
        return JSONResponse(status_code=201, content={"persistent_id": dataset_info['data']['persistentId']})
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
@router.post("/publish/upload/ark:{NAAN}/{postfix}")
async def upload_dataset(
    NAAN: str,
    postfix: str,
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    settings: DataversePublishSettings
):
    ark = f"ark:{NAAN}/{postfix}"

    # Retrieve ROCrate metadata
    rocrate_doc = rocrateCollection.find_one({"@id": ark})
    if not rocrate_doc:
        raise HTTPException(status_code=404, detail="ROCrate not found")

    # Authorization check
    rocrate_group = rocrate_doc.get("permissions", {}).get("group")
    if rocrate_group not in currentUser.memberOf and fairscapeConfig.ldap.adminDN not in currentUser.memberOf:
        raise HTTPException(status_code=401, detail="User not authorized to upload this ROCrate")

    # Retrieve API token
    token_doc = apiTokenCollection.find_one({"user_id": currentUser.cn})
    if not token_doc:
        raise HTTPException(status_code=404, detail="API token not found")
    api_token = APIToken(**token_doc).decrypt_token()

    rocrate = ROCrate(**rocrate_doc)

    # Get the file path from the ROCrate distribution
    file_path = rocrate.distribution.archivedObjectPath
    if not file_path:
        raise HTTPException(status_code=404, detail="No file associated with this ROCrate")

    # Retrieve the file from MinIO
    try:
        file_data = minioClient.get_object(
            bucket_name=fairscapeConfig.minio.rocrate_bucket,
            object_name=file_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file from MinIO: {str(e)}")

    # Upload file to Dataverse
    url = f"{settings.base_url}/api/datasets/:persistentId/add?persistentId={rocrate.persistent_id}"
    headers = {"X-Dataverse-key": api_token}
    files = {'file': (Path(file_path).name, file_data.read(), 'application/zip')}

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        file_info = response.json()
        return JSONResponse(status_code=200, content={"file_id": file_info['data']['files'][0]['dataFile']['id']})
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)