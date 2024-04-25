from typing_extensions import Annotated
from fastapi import (
    APIRouter,
    Header,
    Depends
)
from fastapi.responses import JSONResponse

from fairscape_mds.auth.oauth import getCurrentUser
from fairscape_mds.models.user import (
    User, 
    createUser,
    getUserByGUID,
    listUsers, 
    deleteUserByGUID
)

from fairscape_mds.config import get_fairscape_config


router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_client = fairscapeConfig.CreateMongoClient()
mongo_db = mongo_client[fairscapeConfig.mongo.db]
userCollection = mongo_db[fairscapeConfig.mongo.user_collection]
passwordSalt = fairscapeConfig.passwordSalt


@router.post('/user',
             summary="Create a user",
             response_description="The created user")
def user_create(passedUser: User):
    """
    Create a user with the following properties:

    - **@id**: a unique identifier
    - **@type**: Person
    - **name**: a name
    - **email**: an email
    - **password**: a password
    """

    create_status = createUser(
            passedUser,
            passwordSalt, 
            userCollection)

    if create_status.success: 

        return JSONResponse(
            status_code=201,
            content={
                'created': {
                    '@id': passedUser.guid, 
                    '@type': 'Person', 
                    'name': passedUser.name
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
def user_list(currentUser: Annotated[User, Depends(getCurrentUser)]):
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

    userGUID = f"ark:{NAAN}/{postfix}"
    userInstance, readStatus = getUserByGUID(userGUID, userCollection)

    if readStatus.success:
        return userInstance
    else:
        return JSONResponse(
            status_code=readStatus.status_code, 
            content={
                "error": readStatus.message
            }
        )


#@router.put("/user/ark:{NAAN}/{postfix}",
#            summary="Update a user",
#            response_description="The updated user")
#def user_update(
#    user: User
#):
#    updateUser(passedUser, userCollection)
#    user = User.construct(guid=user_id)
#
#    update_status = user.update(userCollection)
#
#    if update_status.success:
#        return JSONResponse(
#            status_code=200,
#            content={"updated": {"@id": user.id, "@type": "Person", "name": user.name}}
#        )
#    else:
#        return JSONResponse(
#            status_code=update_status.status_code,
#            content={"error": update_status.message}
#        )


@router.delete("/user/ark:{NAAN}/{postfix}",
               summary="Delete a user",
               response_description="The deleted user")
def user_delete(NAAN: str, postfix: str, currentUser: Annotated[User, Depends(getCurrentUser)]):
    """
    Deletes a user based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    userGUID = f"ark:{NAAN}/{postfix}"

    deleted_user = deleteUserByGUID(userGUID, userCollection)

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
