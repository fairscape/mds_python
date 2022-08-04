from fastapi import APIRouter, Response, Header
from fastapi.responses import JSONResponse
from mds.database import mongo, casbin
from mds.models.organization import Organization, list_organization
from mds.models.user import FindUserAuth, UserNotFound
from mds.models.compact.user import UserCompactView

import base64

router = APIRouter()


@router.post("/organization",
             summary="Create a organization",
             response_description="The created organization")
def organization_create(organization: Organization, response: Response, Authorization: str | None = Header(default=None)):
    """
    Create an organization with the following properties:

    - **@id**: a unique identifier
    - **@type**: Organization
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """
    
    enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    authz_header = Authorization.strip("Basic ")
    email, password = str(base64.b64decode(authz_header), 'utf-8').split(":")

    try:
        calling_user = FindUserAuth(mongo_collection, email, password)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )

    # set the calling user as the owner
    organization.owner = UserCompactView(
        id=calling_user.id,
        name=calling_user.name,
        email=calling_user.email)

    create_status = organization.create(mongo_collection)
    mongo_client.close()

    if create_status.success:

        # casbin add policies for ownership to mongo 
        enforcer.add_policy(calling_user.id, "read", organization.id)
        enforcer.add_policy(calling_user.id, "update", organization.id)
        enforcer.add_policy(calling_user.id, "delete", organization.id)
        enforcer.add_policy(calling_user.id, "createProject", organization.id)
        enforcer.add_policy(calling_user.id, "manage", organization.id)
        enforcer.save_policy()

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
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    organization = list_organization(mongo_collection)

    mongo_client.close()

    return organization


@router.get("/organization/ark:{NAAN}/{postfix}",
            summary="Retrieve an organization",
            response_description="The retrieved organization")
def organization_get(
    NAAN: str, 
    postfix: str, 
    response: Response, 
    Authorization: str | None = Header(default=None)):
    """
    Retrieves an organization based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    organization_id = f"ark:{NAAN}/{postfix}"

    enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    authz_header = Authorization.strip("Basic ")
    email, password = str(base64.b64decode(authz_header), 'utf-8').split(":")

    try:
        calling_user = FindUserAuth(mongo_collection, email, password)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )

    if enforcer.enforce(calling_user.id, "read", organization_id) != True:
        return JSONResponse(
            status_code=401,
            content={
                "@id": organization_id,
                "error": "access not granted for read organization"
                }
        )

    organization = Organization.construct(id=organization_id)
    read_status = organization.read(mongo_collection)
    mongo_client.close()

    if read_status.success:
        return organization
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


@router.put("/organization",
            summary="Update an organization",
            response_description="The updated organization")
def organization_update(
    organization: Organization, 
    response: Response,
    Authorization: str | None = Header(default=None)):

    enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']


    authz_header = Authorization.strip("Basic ")
    email, password = str(base64.b64decode(authz_header), 'utf-8').split(":")

    try:
        calling_user = FindUserAuth(mongo_collection, email, password)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )

    if enforcer.enforce(calling_user.id, "update", organization.id) != True:
        return JSONResponse(
            status_code=401,
            content={"error": "user not permitted to update organization"}
        )

    update_status = organization.update(mongo_collection)
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
    Authorization: str | None = Header(default=None)):
    """
    Deletes an organization based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    organization_id = f"ark:{NAAN}/{postfix}"

    enforcer = casbin.GetEnforcer()

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']


    authz_header = Authorization.strip("Basic ")
    email, password = str(base64.b64decode(authz_header), 'utf-8').split(":")

    try:
        calling_user = FindUserAuth(mongo_collection, email, password)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )

    if enforcer.enforce(calling_user.id, "delete", organization_id) != True:
        return JSONResponse(
            status_code=401,
            content={"error": "user not permitted to delete organization"}
        )

    organization = Organization.construct(id=organization_id)
    delete_status = organization.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": organization_id, "@type": "Organization", "name": organization.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
