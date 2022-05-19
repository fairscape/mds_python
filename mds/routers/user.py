from fastapi import APIRouter
from fastapi.responses import JSONResponse
from mds.models.user import User, list_users
from mds.database import mongo

router = APIRouter()


@router.post('/user')
async def user_create(user: User):
    """
    Create a user with the following properties:

    - **@id**
    - **name**
    - **email**
    - **password**
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    create_status = user.create(mongo_collection)

    mongo_client.close()

    if create_status.success:

        return JSONResponse( 
            status_code = 201,
            content = {'created': {'@id': user.id, '@type': 'Person', 'name': user.name}}
            )
    else:
        return JSONResponse(
            status_code = create_status.status_code,
            content = {'error': create_status.message}
        )


@router.get('/user', status_code=200)
async def user_list():
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    users = list_users(mongo_collection)

    mongo_client.close()

    return users


@router.get("/user/ark:{NAAN}/{postfix}")
async def user_get(NAAN: str, postfix: str):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    user_id = f"ark:{NAAN}/{postfix}"

    user = User.construct(id=user_id)

    read_status = user.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return user
    else:
        return JSONResponse(status_code = read_status.status_code, content = {"error": read_status.message})


@router.put("/user")
async def user_update(user: User):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    update_status = user.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": user.id, "@type": "Person", "name": user.name}}

    else:
        return JSONResponse(
            status_code = update_status.status_code,
            content= {"error": update_status.message}
            )


@router.delete("/user/ark:{NAAN}/{postfix}")
async def user_delete(NAAN: str, postfix: str):
    user_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    user = User.construct(id=user_id)

    # read user
    # TODO deal with status errors
    user.read(mongo_collection)

    delete_status = user.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": user_id, "@type": "Person", "name": user.name}}
    else:
        return JSONResponse(
            status_code= delete_status.status_code,
            content = {"error": f"{str(delete_status.message)}"}
        )
