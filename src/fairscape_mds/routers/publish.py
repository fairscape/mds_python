from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query, Body
from fastapi.responses import JSONResponse
from typing import Annotated, Dict
from fairscape_mds.models.user import UserLDAP
from fairscape_mds.auth.oauth import getCurrentUser
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.models.fairscape_base import FairscapeBaseModel 
from fairscape_mds.auth.ldap import getUserTokens
from pathlib import Path
import requests
from datetime import datetime

# License mapping based on dataverse options
LICENSE_MAP = {
    "CC0 1.0": {
        "name": "CC0 1.0",
        "uri": "http://creativecommons.org/publicdomain/zero/1.0"
    },
    "CC BY 4.0": {
        "name": "CC BY 4.0",
        "uri": "https://creativecommons.org/licenses/by/4.0"
    },
    "CC BY-SA 4.0": {
        "name": "CC BY-SA 4.0",
        "uri": "https://creativecommons.org/licenses/by-sa/4.0"
    },
    "CC BY-NC 4.0": {
        "name": "CC BY-NC 4.0",
        "uri": "https://creativecommons.org/licenses/by-nc/4.0"
    },
    "CC BY-NC-SA 4.0": {
        "name": "CC BY-NC-SA 4.0",
        "uri": "https://creativecommons.org/licenses/by-nc-sa/4.0"
    },
    "CC BY-ND 4.0": {
        "name": "CC BY-ND 4.0",
        "uri": "https://creativecommons.org/licenses/by-nd/4.0"
    },
    "CC BY-NC-ND 4.0": {
        "name": "CC BY-NC-ND 4.0",
        "uri": "https://creativecommons.org/licenses/by-nc-nd/4.0"
    }
}

DEFAULT_LICENSE = "CC BY 4.0"
DEFAULT_DATAVERSE_URL = "https://dataversedev.internal.lib.virginia.edu/"
DEFAULT_DATAVERSE_DB = "libradata"

router = APIRouter()

fairscapeConfig = get_fairscape_config()

minioClient = fairscapeConfig.CreateMinioClient()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]

@router.post("/publish/create/ark:{NAAN}/{postfix}")
async def create_dataset(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str,
    postfix: str,
    userProvidedMetadata: dict = Body(default={}),
    dataverse_url: str | None = Query(default=None, description="Custom Dataverse URL"),
    database: str | None = Query(default=None, description="Custom database name")
):
    dataverse_url = dataverse_url or DEFAULT_DATAVERSE_URL
    dataverse_db = database or DEFAULT_DATAVERSE_DB

    # Get user's tokens and find matching Dataverse token
    tokens = getUserTokens(fairscapeConfig.ldap.connectAdmin(), currentUser.dn)
    api_token = None
    for token in tokens:
        if token.endpointURL == dataverse_url:
            api_token = token.tokenValue
            break
    
    if not api_token:
        raise HTTPException(
            status_code=401,
            detail=f"No token found for Dataverse instance: {dataverse_url}. Please add your token first."
        )
    
    rocrateGUID = f"ark:{NAAN}/{postfix}"
    rocrateMetadata = rocrateCollection.find_one(
        {"@id": rocrateGUID}, 
        projection={"_id": 0}
        )
    
    if rocrateMetadata is None:
        return JSONResponse(
            status_code=404,
            content={
                "@id": f"{fairscapeConfig.url}/{rocrateGUID}",
                "error": f"unable to find record for RO-Crate: {rocrateGUID}"
            }
        )

    # AuthZ: check if user is allowed to download 
    # if a user is a part of the group that uploaded the ROCrate OR user is an Admin
    rocrateGroup = rocrateMetadata.get("permissions", {}).get("group")
    if rocrateGroup not in currentUser.memberOf and fairscapeConfig.ldap.adminDN not in currentUser.memberOf:
        raise HTTPException(status_code=401, detail="User not authorized to publish this ROCrate")

    # Get license from user metadata or use default
    license_name = userProvidedMetadata.get("license", DEFAULT_LICENSE)
    if license_name not in LICENSE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid license. Please choose from: {', '.join(LICENSE_MAP.keys())}"
        )
    
    license_info = LICENSE_MAP[license_name]
    dataverseMetadata = rocrateMetadata | userProvidedMetadata

    # Prepare dataset metadata
    metadata = {
        "datasetVersion": {
            "license": license_info,
            "metadataBlocks": {
                "citation": {
                    "fields": [
                        {"value": dataverseMetadata.get("name"), "typeClass": "primitive", "multiple": False, "typeName": "title"},
                        {
                            "value": [
                                {
                                    "authorName": {"value": author, "typeClass": "primitive", "multiple": False, "typeName": "authorName"},
                                    "authorAffiliation": {"value": "CAMA", "typeClass": "primitive", "multiple": False, "typeName": "authorAffiliation"}
                                } for author in dataverseMetadata.get("author").split(', ')
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "author"
                        },
                        {
                            "value": [
                                {
                                    "datasetContactName": {"value": currentUser.cn, "typeClass": "primitive", "multiple": False, "typeName": "datasetContactName"},
                                    "datasetContactEmail": {"value": currentUser.email, "typeClass": "primitive", "multiple": False, "typeName": "datasetContactEmail"}
                                }
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "datasetContact"
                        },
                        {
                            "value": [
                                {
                                    "dsDescriptionValue": {"value": dataverseMetadata.get("description"), "typeClass": "primitive", "multiple": False, "typeName": "dsDescriptionValue"}
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
                                } for keyword in dataverseMetadata.get("keywords").split(',')
                            ],
                            "typeClass": "compound",
                            "multiple": True,
                            "typeName": "keyword"
                        },
                        {"value": "This dataset is part of a ROCrate.", "typeClass": "primitive", "multiple": False, "typeName": "notesText"},
                        {"typeName": "datasetPublicationDate", "multiple": False, "typeClass": "primitive", "value": dataverseMetadata.get("datePublished", datetime.today().strftime("%Y-%m-%d"))},
                        {"typeName": "productionDate", "multiple": False, "typeClass": "primitive", "value": dataverseMetadata.get("datePublished", datetime.today().strftime("%Y-%m-%d"))}
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
    url = f"{dataverse_url}/api/dataverses/{dataverse_db}/datasets"
    response = requests.post(url, headers=headers, json=metadata)

    if response.status_code == 201:
        dataset_info = response.json()
        persistent_id = dataset_info['data']['persistentId']
        
        rocrate = FairscapeBaseModel(
            guid=rocrateGUID,
            metadataType=rocrateMetadata.get("@type"),
            name=rocrateMetadata.get("name"),
            identifier=persistent_id
        )
        
        update_result = rocrate.update(rocrateCollection)
        if not update_result.success:
            print(f"Failed to update ROCrate with identifier: {update_result.message}")
            
        return JSONResponse(
            status_code=201, 
            content={
                "persistent_id": persistent_id,
                "rocrate_update": update_result.success
            }
        )
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
@router.post("/publish/upload/ark:{NAAN}/{postfix}")
async def upload_dataset(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str,
    postfix: str,
    dataverse_url: str | None = Query(default=None, description="Custom Dataverse URL")
):
    dataverse_url = dataverse_url or DEFAULT_DATAVERSE_URL

    # Get user's tokens and find matching Dataverse token
    tokens = getUserTokens(fairscapeConfig.ldap.connectAdmin(), currentUser.dn)
    api_token = None
    for token in tokens:
        if token.endpointURL == dataverse_url:
            api_token = token.tokenValue
            break
    
    if not api_token:
        raise HTTPException(
            status_code=401,
            detail=f"No token found for Dataverse instance: {dataverse_url}. Please add your token first."
        )
    
    rocrateGUID = f"ark:{NAAN}/{postfix}"
    rocrateMetadata = rocrateCollection.find_one(
        {"@id": rocrateGUID}, 
        projection={"_id": 0}
        )
    
    if rocrateMetadata is None:
        return JSONResponse(
            status_code=404,
            content={
                "@id": f"{fairscapeConfig.url}/{rocrateGUID}",
                "error": f"unable to find record for RO-Crate: {rocrateGUID}"
            }
        )

    # AuthZ: check if user is allowed to download 
    rocrateGroup = rocrateMetadata.get("permissions", {}).get("group")
    if rocrateGroup not in currentUser.memberOf and fairscapeConfig.ldap.adminDN not in currentUser.memberOf:
        raise HTTPException(status_code=401, detail="User not authorized to publish this ROCrate")

    # Check if the ROCrate has a Dataverse identifier
    persistent_id = rocrateMetadata.get("identifier")
    if not persistent_id:
        raise HTTPException(
            status_code=400,
            detail="Dataset has not been created in Dataverse yet. Please create the dataset first using the create endpoint."
        )

    # Get the file path from the ROCrate distribution
    file_path = rocrateMetadata.get("distribution", {}).get("archivedObjectPath")
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

    # Upload file to Dataverse using the persistent ID
    url = f"{dataverse_url}api/datasets/:persistentId/add?persistentId={persistent_id}"
    headers = {"X-Dataverse-key": api_token}
    
    try:
        files = {'file': (Path(file_path).name, file_data.read(), 'application/zip')}
        response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            file_info = response.json()
            return JSONResponse(
                status_code=200, 
                content={
                    "persistent_id": persistent_id,
                    "file_id": file_info['data']['files'][0]['dataFile']['id']
                }
            )
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Error uploading file to Dataverse: {response.text}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during file upload: {str(e)}"
        )