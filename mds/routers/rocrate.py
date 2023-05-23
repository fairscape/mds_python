from fastapi import APIRouter
from fastapi.responses import JSONResponse
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

from mds.database import mongo
from mds.models.rocrate import ROCrate, list_rocrate

router = APIRouter()


@router.post("/rocrate",
             summary="Create an ROCrate",
             response_description="The created rocrate")
def rocrate_create(rocrate: ROCrate):
    """
    Create a rocrate with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:ROCrate
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """
    mongo_client = mongo.GetConfig()
    create_status = rocrate.create(mongo_client)

    mongo_client.close()

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": rocrate.id, "@type": "evi:ROCrate"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )



@router.get("/rocrate",
            summary="List all rocrates",
            response_description="Retrieved list of rocrates")
def rocrate_list():
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    rocrate = list_rocrate(mongo_collection)

    mongo_client.close()

    return rocrate



@router.get("/rocrate/ark:{NAAN}/{postfix}",
            summary="Retrieve a rocrate",
            response_description="The retrieved rocrate")
def rocrate_get(NAAN: str, postfix: str):
    """
    Retrieves a rocrate based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    rocrate_id = f"ark:{NAAN}/{postfix}"

    rocrate = ROCrate.construct(id=rocrate_id)

    read_status = rocrate.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return rocrate
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )


@router.put("/rocrate",
            summary="Update a rocrate",
            response_description="The updated rocrate")
def rocrate_update(rocrate: ROCrate):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    update_status = rocrate.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": rocrate.id, "@type": "evi:ROCrate"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )



@router.delete("/rocrate/ark:{NAAN}/{postfix}",
               summary="Delete a rocrate",
               response_description="The deleted rocrate")
def rocrate_delete(NAAN: str, postfix: str):
    """
    Deletes a rocrate based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    rocrate_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    rocrate = ROCrate.construct(id=rocrate_id)

    delete_status = rocrate.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": rocrate_id, "@type": "evi:ROCrate", "name": rocrate.name}}
        )

    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
