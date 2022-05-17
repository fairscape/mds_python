from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.organization import Organization, list_organization

router = APIRouter()


@router.post("/organization")
def organization_create(organization: Organization, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = organization.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": organization.id, "@type": "organization"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/organization")
def organization_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    organization = list_organization(mongo_collection)

    mongo_client.close()

    return organization


@router.get("/organization/ark:{NAAN}/{postfix}")
def organization_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    organization_id = f"ark:{NAAN}/{postfix}"

    organization = Organization.construct(id=organization_id)

    read_status = organization.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return organization
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/organization")
def organization_update(organization: Organization, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = organization.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": organization.id, "@type": "organization"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/organization/ark:{NAAN}/{postfix}")
def organization_delete(NAAN: str, postfix: str):
    organization_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    organization = Organization.construct(id=organization_id)

    delete_status = organization.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": organization_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
