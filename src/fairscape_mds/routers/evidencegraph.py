from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from fairscape_mds.models.evidencegraph import EvidenceGraph, list_evidencegraph
from fairscape_mds.config import (
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
) 
router = APIRouter()


@router.post("/evidencegraph",
             summary="Create a evidencegraph",
             response_description="The created evidencegraph")
def evidencegraph_create(evidencegraph: EvidenceGraph, response: Response):
    """
    Create an evidencegraph with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:EvidenceGraph
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """
    mongo_client = get_mongo_client()
    mongo_config = get_mongo_config()
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    create_status = evidencegraph.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": evidencegraph.guid, "@type": "evi:EvidenceGraph"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/evidencegraph",
            summary="List all evidencegraphs",
            response_description="Retrieved list of evidencegraphs")
def evidencegraph_list(response: Response):
    mongo_client = get_mongo_client()
    mongo_config = get_mongo_config()
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    evidencegraph = list_evidencegraph(mongo_collection)

    return evidencegraph


@router.get("/evidencegraph/ark:{NAAN}/{postfix}",
            summary="Retrieve an evidencegraph",
            response_description="The retrieved evidencegraph")
def evidencegraph_get(NAAN: str, postfix: str, response: Response):
    """
    Retrieves an evidencegraph based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = get_mongo_client()
    mongo_config = get_mongo_config()
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    evidencegraph_id = f"ark:{NAAN}/{postfix}"

    evidencegraph = EvidenceGraph.construct(id=evidencegraph_id)

    read_status = evidencegraph.read(mongo_collection)

    if read_status.success:
        return evidencegraph
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


@router.put("/evidencegraph",
            summary="Update an evidencegraph",
            response_description="The updated evidencegraph")
def evidencegraph_update(evidencegraph: EvidenceGraph, response: Response):
    mongo_client = get_mongo_client()
    mongo_config = get_mongo_config()
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    update_status = evidencegraph.update(mongo_collection)

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": evidencegraph.guid, "@type": "evi:EvidenceGraph"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/evidencegraph/ark:{NAAN}/{postfix}",
               summary="Delete an evidencegraph",
               response_description="The deleted evidencegraph")
def evidencegraph_delete(NAAN: str, postfix: str):
    """
    Deletes an evidencegraph based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    evidencegraph_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    evidencegraph = EvidenceGraph.construct(id=evidencegraph_id)

    delete_status = evidencegraph.delete(mongo_collection)

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": evidencegraph_id, "@type": "evi:EvidenceGraph", "name": evidencegraph.name}}
        )

    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
