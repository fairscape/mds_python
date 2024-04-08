from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from fairscape_mds.mds.models.software import Software, listSoftware, createSoftware, deleteSoftware
from fairscape_mds.mds.config import (
        get_mongo_config,
        get_mongo_client,
        )

router = APIRouter()

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

mongo_db = mongo_client[mongo_config.db]
identifierCollection = mongo_db[mongo_config.identifier_collection]
userCollection = mongo_db[mongo_config.user_collection]


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

    create_status = createSoftware(software, identifierCollection, userCollection)

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": software.model_dump(by_alias=True)}
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
    software = listSoftware(identifierCollection)
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

    software_id = f"ark:{NAAN}/{postfix}"

    software = Software.construct(guid=software_id)

    read_status = software.read(identifierCollection)

    if read_status.success:
        return software
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


@router.put("/software",
            summary="Update a software",
            response_description="The updated software")
def software_update(software: Software, response: Response):
    update_status = software.update(identifier_collection)

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
    softwareGUID = f"ark:{NAAN}/{postfix}"

    deleteStatus = deleteSoftware(
            softwareGUID, 
            identifierCollection, 
            userCollection
            )

    if deleteStatus.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": software_id, "@type": "evi:Software", "name": software.name}}
        )
    else:
        return JSONResponse(
            status_code=deleteStatus.status_code,
            content={"error": f"{str(deleteStatus.message)}"}
        )
