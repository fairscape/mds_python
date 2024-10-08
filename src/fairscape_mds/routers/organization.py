from typing import Union
from fastapi import APIRouter, Response, Header
from fastapi.responses import JSONResponse
import base64

from fairscape_mds.models.organization import Organization, list_organization
from fairscape_mds.models.auth import ParseAuthHeader, UserNotFound, TokenError

from fairscape_mds.config import (
    get_fairscape_config
) 


router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]

@router.post("/organization",
             summary="Create a organization",
             response_description="The created organization")
def organization_create(
    organization: Organization, 
    Authorization: Union[str, None] = Header(default=None)
    ):
    """
    Create an organization with the following properties:

    - **@id**: a unique identifier
    - **@type**: Organization
    - **name**: a name
    - **owner**: an existing user @id
    """
    
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    try:
        calling_user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )

    # set the calling user as the owner
    organization.owner = calling_user.id,
    create_status = organization.create(mongo_client)
    mongo_client.close()

    if create_status.success:

        return JSONResponse(
            status_code=201,
            content={"created": {"@id": organization.id, "@type": "Organization"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/organization",
            summary="List all organizations",
            response_description="Retrieved list of organizations")
def organization_list(response: Response):
    mongo_client = mongo.GetConfig()
    organization = list_organization(mongo_client)
    mongo_client.close()

    return organization


@router.get("/organization/ark:{NAAN}/{postfix}",
            summary="Retrieve an organization",
            response_description="The retrieved organization")
def organization_get(
    NAAN: str, 
    postfix: str, 
    Authorization: Union[str, None] = Header(default=None)):
    """
    Retrieves an organization based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    organization_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    
    #enforcer = casbin.GetEnforcer()

    # decode the credentials and find the user
    try:
        calling_user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )


    organization = Organization.construct(id=organization_id)
    read_status = organization.read(mongo_client)
    mongo_client.close()

    if read_status.success:
        return organization
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
            )


@router.put("/organization",
            summary="Update an organization",
            response_description="The updated organization")
def organization_update(
    organization: Organization, 
    Authorization: Union[str, None] = Header(default=None)
    ):

    #enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    # decode the credentials and find the user
    try:
        calling_user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )

    update_status = organization.update(mongo_client)
    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": organization.id, "@type": "Organization"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/organization/ark:{NAAN}/{postfix}",
               summary="Delete an organization",
               response_description="The deleted organization")
def organization_delete(
    NAAN: str, 
    postfix: str,
    Authorization: Union[str, None] = Header(default=None)):
    """
    Deletes an organization based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    organization_id = f"ark:{NAAN}/{postfix}"

    #enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]


    # decode the credentials and find the user
    try:
        calling_user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )


    organization = Organization.construct(id=organization_id)
    delete_status = organization.delete(mongo_client)
    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {
                "@id": organization_id, 
                "@type": "Organization", 
                "name": organization.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
