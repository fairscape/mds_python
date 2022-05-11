from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.software import Software, list_software

router = APIRouter()


@router.post("/software")
def software_create(software: Software, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = software.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": software.id, "@type": "evi:Software"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/software")
def software_list(response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    software = list_software(mongo_collection)

    mongo_client.close()

    return software


@router.get("/software/ark:{NAAN}/{postfix}")
def software_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    software_id = f"ark:{NAAN}/{postfix}"

    software = Software.construct(id=software_id)

    read_status = software.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return software
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/software")
def software_update(software: Software, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = software.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": software.id, "@type": "evi:Software"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/software/ark:{NAAN}/{postfix}")
def software_delete(NAAN: str, postfix: str):
    software_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    software = Software.construct(id=software_id)

    delete_status = software.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": software_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
