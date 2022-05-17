from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.computation import Computation, list_computation

router = APIRouter()


@router.post("/computation")
def computation_create(computation: Computation, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = computation.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": computation.id, "@type": "evi:Computation"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/computation")
def computation_list(response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    computation = list_computation(mongo_collection)

    mongo_client.close()

    return computation


@router.get("/computation/ark:{NAAN}/{postfix}")
def computation_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    computation_id = f"ark:{NAAN}/{postfix}"

    computation = Computation.construct(id=computation_id)

    read_status = computation.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return computation
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/computation")
def computation_update(computation: Computation, response: Response):
    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = computation.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": computation.id, "@type": "evi:Computation"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/computation/ark:{NAAN}/{postfix}")
def computation_delete(NAAN: str, postfix: str):
    computation_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.get_config()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    computation = Computation.construct(id=computation_id)

    delete_status = computation.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": computation_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
