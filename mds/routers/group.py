from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from mds.database import mongo
from mds.models.group import Group, list_groups
from mds.models.compact.user import UserCompactView

router = APIRouter()


@router.post("/group")
async def group_create(group: Group):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = group.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": group.id, "@type": "Organization"}}
    else:
        return JSONResponse( 
            status_code = create_status.status_code, 
            content ={"error": create_status.message}
            )


@router.get("/group")
def group_list():
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    groups = list_groups(mongo_collection)

    mongo_client.close()

    return groups


@router.get("/group/ark:{NAAN}/{postfix}")
def group_get(NAAN: str, postfix: str):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    group_id = f"ark:{NAAN}/{postfix}"

    group = Group.construct(id=group_id)

    read_status = group.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return group
    else:
        return JSONResponse( 
            status_code = read_status.status_code, 
            content ={"error": read_status.message}
            )


@router.put("/group")
def group_update(group: Group, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = group.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": group.id, "@type": "Organization"}}
    else:
        return JSONResponse( 
            status_code = update_status.status_code, 
            content ={"error": update_status.message}
            )


@router.delete("/group/ark:{NAAN}/{postfix}")
def group_delete(NAAN: str, postfix: str):
    group_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']


    # TODO delete function should have FindOneAndDelete
    group = Group.construct(id=group_id)
    group.read(mongo_collection)
    delete_status = group.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": group_id, "@type": "Organization", "name":  group.name}}
    else:
        return JSONResponse( 
            status_code = delete_status.status_code, 
            content ={"error": delete_status.message}
            )


@router.put("/group/ark:{NAAN}/{postfix}/addUser/")
def group_add_user(NAAN: str, postfix: str, user: UserCompactView):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    group_id = f"ark:{NAAN}/{postfix}"
    group = Group.construct(id=group_id)

    member_id = user.id
    add_user_status = group.add_user(mongo_collection, member_id)

    mongo_client.close()

    if add_user_status.success:
        return JSONResponse(
            status_code = 201,
            content = {"updated": {"@id": group.id, "@type": "Organization", "name": group.name}}
            )
    else:
        return JSONResponse( 
            status_code = add_user_status.status_code, 
            content ={"error": add_user_status.message}
            )


@router.put("/group/ark:{NAAN}/{postfix}/rmUser/")
def group_remove_user(NAAN: str, postfix: str, user: UserCompactView):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    group_id = f"ark:{NAAN}/{postfix}"
    group = Group.construct(id=group_id)

    member_id = user.id
    add_user_status = group.remove_user(mongo_collection, member_id)

    mongo_client.close()

    if add_user_status.success:
        return JSONResponse(
            status_code = 201,
            content = {"updated": {"@id": group.id, "@type": "Organization", "name": group.name}}
            )
    else:
        return JSONResponse( 
            status_code = add_user_status.status_code, 
            content ={"error": add_user_status.message}
            )
