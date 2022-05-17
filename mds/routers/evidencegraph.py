from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.evidencegraph import EvidenceGraph, list_evidencegraph

router = APIRouter()


@router.post("/evidencegraph")
def evidencegraph_create(evidencegraph: EvidenceGraph, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = evidencegraph.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": evidencegraph.id, "@type": "evi:EvidenceGraph"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/evidencegraph")
def evidencegraph_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    evidencegraph = list_evidencegraph(mongo_collection)

    mongo_client.close()

    return evidencegraph


@router.get("/evidencegraph/ark:{NAAN}/{postfix}")
def evidencegraph_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    evidencegraph_id = f"ark:{NAAN}/{postfix}"

    evidencegraph = EvidenceGraph.construct(id=evidencegraph_id)

    read_status = evidencegraph.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return evidencegraph
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/evidencegraph")
def evidencegraph_update(evidencegraph: EvidenceGraph, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = evidencegraph.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": evidencegraph.id, "@type": "evi:EvidenceGraph"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/evidencegraph/ark:{NAAN}/{postfix}")
def evidencegraph_delete(NAAN: str, postfix: str):
    evidencegraph_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    evidencegraph = EvidenceGraph.construct(id=evidencegraph_id)

    delete_status = evidencegraph.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": evidencegraph_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
