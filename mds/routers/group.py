from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from mds.models.group import Group, list_groups

from mds.config import (
    get_minio,
    get_casbin_config,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
    CasbinConfig
) 

router = APIRouter()

# setup database clients
mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

casbin_enforcer = get_casbin_enforcer()
casbin_enforcer.load_policy()


@router.post("/group",
             summary="Create a group",
             response_description="The created group")
async def group_create(group: Group):
    """
    Create a group with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Organization
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    create_status = group.create(mongo_collection)

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": group.id, 
                    "@type": "Organization", 
                    "name": group.name
                }
            }
        )

    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/group",
            summary="List all groups",
            response_description="Retrieved list of groups")
def group_list():
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    groups = list_groups(mongo_collection)

    return groups


@router.get("/group/ark:{NAAN}/{postfix}",
            summary="Retrieve a group",
            response_description="The retrieved group")
def group_get(NAAN: str, postfix: str):
    """
    Retrieves a group based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    group_id = f"ark:{NAAN}/{postfix}"

    group = Group.construct(id=group_id)

    read_status = group.read(mongo_collection)

    if read_status.success:
        return group

    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )


@router.put("/group",
            summary="Update a group",
            response_description="The updated group")
def group_update(group: Group):
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    update_status = group.update(mongo_collection)

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={
                "updated": {
                    "@id": group.id, 
                    "@type": "Organization"
                }
            }
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/group/ark:{NAAN}/{postfix}",
               summary="Delete a group",
               response_description="The deleted group")
def group_delete(NAAN: str, postfix: str):
    """
    Deletes a group based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    # TODO delete function should have FindOneAndDelete
    group_id = f"ark:{NAAN}/{postfix}"
    group = Group.construct(id=group_id)

    delete_status = group.delete(mongo_collection)

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": {
                    "@id": group_id, 
                    "@type": "Organization", 
                    "name": group.name
                }
            }
        )

    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )


@router.put("/group/ark:{NAAN}/{postfix}/addUser/",
            summary="Add user to a group",
            response_description="The updated group")
def group_add_user(NAAN: str, postfix: str, userID: str):
    """
    Add member to a group based on a given group identifier and member data:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    group_id = f"ark:{NAAN}/{postfix}"
    group = Group.construct(id=group_id)

    member_id = user.id
    add_user_status = group.add_user(mongo_collection, member_id)

    mongo_client.close()

    if add_user_status.success:
        return JSONResponse(
            status_code=201,
            content={"updated": {"@id": group.id, "@type": "Organization", "name": group.name}}
        )
    else:
        return JSONResponse(
            status_code=add_user_status.status_code,
            content={"error": add_user_status.message}
        )


@router.put("/group/ark:{NAAN}/{postfix}/rmUser/",
            summary="Remove user from a group",
            response_description="The updated group")
def group_remove_user(NAAN: str, postfix: str, userId: str):
    """
    Remove member from a group based on a given group identifier and member data:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    group_id = f"ark:{NAAN}/{postfix}"
    group = Group.construct(id=group_id)

    member_id = userId
    add_user_status = group.remove_user(mongo_collection, member_id)

    mongo_client.close()

    if add_user_status.success:
        return JSONResponse(
            status_code=201,
            content={"updated": {"@id": group.id, "@type": "Organization", "name": group.name}}
        )
    else:
        return JSONResponse(
            status_code=add_user_status.status_code,
            content={"error": add_user_status.message}
        )
