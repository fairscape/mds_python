from typing_extensions import Annotated

from fastapi import (
    APIRouter,
    Header,
    Depends
)
from fastapi.responses import JSONResponse

from fairscape_mds.mds.models.user import User, listUsers, deleteUserByGUID
from fairscape_mds.mds.config import (
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
) 

router = APIRouter()

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()
mongo_db = mongo_client[mongo_config.db]
userCollection = mongo_db[mongo_config.user_collection]


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


    create_status = user.create(userCollection)

    if create_status.success:

        # create permissions for casbin
        # fairscape_mds.mds.auth.casbin.createUser(
        #     casbin_enforcer,
        #     user.email,
        #     user.id
        # )
        # casbin_enforcer.save_policy()
        

        return JSONResponse(
            status_code=201,
            content={
                'created': {
                    '@id': user.guid, 
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
    users = listUsers(userCollection)
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

    user_id = f"ark:{NAAN}/{postfix}"

    user = User.construct(guid=user_id)
    read_status = user.read(userCollection)

    if read_status.success:
        return user
    else:
        return JSONResponse(
            status_code=read_status.status_code, 
            content={
                "error": read_status.message
            }
        )


@router.put("/user/ark:{NAAN}/{postfix}",
            summary="Update a user",
            response_description="The updated user")
def user_update(
    user: User
):

    user_id = f"ark:{NAAN}/{postfix}"
    user = User.construct(guid=user_id)

    update_status = user.update(userCollection)

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
def user_delete(NAAN: str, postfix: str):
    """
    Deletes a user based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    user_id = f"ark:{NAAN}/{postfix}"


    deleted_user = deleteUserByGUID(userCollection, user_id)

    if deleted_user is None:
        return JSONResponse(
            status_code=404,
            content={"error": "user not found"}
        )
    else:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": {
                    "@id": deleted_user.get("@id"),
                    "@type": deleted_user.get("@type"),
                    "name": deleted_user.get("name"),
                    "email": deleted_user.get("email"),
                    "datasets": deleted_user.get("datasets"),
                    "software": deleted_user.get("software"),
                    "datasets": deleted_user.get("datasets"),
                    "computatations": deleted_user.get("computations"),
                    "rocrates": deleted_user.get("rocrates"),
                    "evidencegraphs": deleted_user.get("evidencegraphs")
                    }
            }
        )
