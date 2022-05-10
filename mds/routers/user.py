from fastapi import APIRouter, Response
from mds.models.user import User, list_users
from mds.database import mongo

router = APIRouter()


@router.post('/user', status_code=201)
def user_create(user: User, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    create_status = user.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {'created': {'@id': user.id, 'type': 'Person'}}
    else:
        response.status_code = create_status.status_code
        return {'error': create_status.message}


@router.get('/user')
def user_list():
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    users = list_users(mongo_collection)

    mongo_client.close()

    return users


@router.get("/user/ark:{NAAN}/{postfix}")
def user_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    user_id = f"ark:{NAAN}/{postfix}"

    user = User.construct(id=user_id)

    read_status = user.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return user
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/user")
def user_update(user: User, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    update_status = user.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": user.id, "@type": "Person"}}

    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/user/ark:{NAAN}/{postfix}")
def user_delete(NAAN: str, postfix: str):
    user_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    user = User.construct(id=user_id)

    delete_status = user.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": user_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
