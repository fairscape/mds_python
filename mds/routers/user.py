from typing import Annotated

from fastapi import (
    APIRouter,
    Header
)
from fastapi.responses import JSONResponse
from mds.models.user import User, list_users
from mds.database import mongo
from mds.database.config import (
    MONGO_DATABASE, 
    MONGO_COLLECTION
)
from mds.config import (
    get_minio,
    get_casbin,
    get_mongo,
    MongoConfig,
    CasbinConfig
) 

import mds.auth.casbin


router = APIRouter()

mongo_config = get_mongo()
mongo_client = mongo_config.CreateClient()

casbin_config = get_casbin()
casbin_enforcer = casbin_config.CreateClient()
casbin_enforcer.load_policy()


@router.post('/user',
             summary="Create a user",
             response_description="The created user")
def user_create(user: User):
    """
    Create a user with the following properties:

    - **@id**: a unique identifier
    - **@type**: Person
    - **name**: a name
    - **email**: an email
    - **password**: a password
    """

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.collection]

    create_status = user.create(mongo_collection)


    if create_status.success:

        # create permissions for casbin
        mds.auth.casbin.createUser(
            casbin_enforcer,
            user.email,
            user.guid
        )
        casbin_enforcer.save_policy()
        

        return JSONResponse(
            status_code=201,
            content={
                'created': {
                    '@id': user.id, 
                    '@type': 'Person', 
                    'name': user.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={'error': create_status.message}
        )


@router.get('/user', status_code=200,
            summary="List all users",
            response_description="Retrieved list of users")
def user_list():

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.collection]

    users = list_users(mongo_collection)

    mongo_client.close()

    return users


@router.get("/user/ark:{NAAN}/{postfix}",
            summary="Retrieve a user",
            response_description="The retrieved user")
async def user_get(NAAN: str, postfix: str):
    """
    Retrieves a user based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    user_id = f"ark:{NAAN}/{postfix}"

    user = User.construct(id=user_id)

    read_status = user.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return user
    else:
        return JSONResponse(status_code=read_status.status_code, content={"error": read_status.message})


@router.put("/user",
            summary="Update a user",
            response_description="The updated user")
async def user_update(user: User):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    update_status = user.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": user.id, "@type": "Person", "name": user.name}}
        )

    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/user/ark:{NAAN}/{postfix}",
               summary="Delete a user",
               response_description="The deleted user")
async def user_delete(NAAN: str, postfix: str):
    """
    Deletes a user based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    user_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    user = User.construct(id=user_id)

    # TODO deal with status errors

    delete_status = user.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": user_id, "@type": "Person", "name": user.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
