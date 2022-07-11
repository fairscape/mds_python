from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from mds.database import mongo
from mds.models.software import Software, list_software

router = APIRouter()


@router.post("/software",
             summary="Create a software",
             response_description="The created software")
def software_create(software: Software, response: Response):
    """
    Create a software with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Software
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = software.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": software.id, "@type": "evi:Software"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/software",
            summary="List all software",
            response_description="Retrieved list of software")
def software_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    software = list_software(mongo_collection)

    mongo_client.close()

    return software


@router.get("/software/ark:{NAAN}/{postfix}",
            summary="Retrieve a software",
            response_description="The retrieved software")
def software_get(NAAN: str, postfix: str, response: Response):
    """
    Retrieves a software based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    software_id = f"ark:{NAAN}/{postfix}"

    software = Software.construct(id=software_id)

    read_status = software.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return software
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


@router.put("/software",
            summary="Update a software",
            response_description="The updated software")
def software_update(software: Software, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = software.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": software.id, "@type": "evi:Software"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/software/ark:{NAAN}/{postfix}",
               summary="Delete a software",
               response_description="The deleted software")
def software_delete(NAAN: str, postfix: str):
    """
    Deletes a software based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    software_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    software = Software.construct(id=software_id)

    delete_status = software.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": software_id, "@type": "evi:Software", "name": software.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
