from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.group import Group, list_groups

router = APIRouter()


@router.post("/group")
def group_create(group: Group, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = group.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": group.id, "@type": "Organization"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/group")
def group_list():
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    groups = list_groups(mongo_collection)

    mongo_client.close()

    return groups


@router.get("/group/ark:{NAAN}/{postfix}")
def group_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    group_id = f"ark:{NAAN}/{postfix}"

    group = Group.construct(id=group_id)

    read_status = group.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return group
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/group")
def group_update(group: Group, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = group.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": group.id, "@type": "Organization"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/group/ark:{NAAN}/{postfix}")
def group_delete(NAAN: str, postfix: str):
    group_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    group = Group.construct(id=group_id)

    delete_status = group.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": group_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}


#
# TODO fix errors during user add
#
@router.put("/group/ark:{NAAN}/{postfix}/addUser/")
def group_add_user(group: Group, NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    member_id = f"ark:{NAAN}/{postfix}"

    add_user_status = group.add_user(mongo_collection, member_id)

    mongo_client.close()

    if add_user_status.success:
        return {"updated": {"@id": group.id, "@type": "Organization"}}
    else:
        response.status_code = add_user_status.status_code
        return {"error": add_user_status.message}
