from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse

from fairscape_mds.models.software import (
        Software, 
        SoftwareCreateModel,
        listSoftware, 
        createSoftware, 
        deleteSoftware,
        getSoftware
        )

from fairscape_mds.config import (
        get_fairscape_config
        )
from fairscape_mds.models.user import (
        User
        )

from typing import Annotated
from fairscape_mds.auth.oauth import getCurrentUser

router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_client = fairscapeConfig.CreateMongoClient()
mongo_db = mongo_client[fairscapeConfig.mongo.db]
userCollection = mongo_db[fairscapeConfig.mongo.user_collection]
identifierCollection = mongo_db[fairscapeConfig.mongo.identifier_collection]


@router.post(
    "/software",
    summary="Create a software",
    )
def software_create(
        currentUser: Annotated[User, Depends(getCurrentUser)],
        softwareInstance: SoftwareCreateModel, 
    ):
    """
    Create a software with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Software
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """

    softwareInstance.owner = currentUser.guid

    softwareInstance = software.convert()
    create_status = createSoftware(softwareInstance, identifierCollection, userCollection)

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": softwareInstance.model_dump(
                by_alias=True, 
                include=['guid', 'name', 'description', 'metadataType', 'author']
                )
                }
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get(
    "/software",
    summary="List all software",
    response_description="Retrieved list of software"
    )
def software_list(
    currentUser: Annotated[User, Depends(getCurrentUser)]
    ):
    softwareList = listSoftware(identifierCollection)
    return softwareList


@router.get("/software/ark:{NAAN}/{postfix}",
            summary="Retrieve a software",
            response_description="The retrieved software")
def software_get(NAAN: str, postfix: str):
    """
    Retrieves a software based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    softwareGUID = f"ark:{NAAN}/{postfix}"

    software, read_status = getSoftware(softwareGUID, identifierCollection)

    if read_status.success:
        return software
    else:
        return JSONResponse(
                status_code=read_status.status_code,
                content={"error": read_status.message}
                )


#@router.put("/software",
#            summary="Update a software",
#            response_description="The updated software")
#def software_update(software: Software, response: Response):
#    update_status = software.update(identifier_collection)
#
#    if update_status.success:
#        return JSONResponse(
#            status_code=200,
#            content={"updated": {"@id": software.guid, "@type": "evi:Software"}}
#        )
#    else:
#        return JSONResponse(
#            status_code=update_status.status_code,
#            content={"deleted": software.model_dump(by_alias=True, include=['guid', 'name', 'description', 'metadataType', 'author'])}
#        )


@router.delete(
    "/software/ark:{NAAN}/{postfix}",
    summary="Delete a software",
    response_description="The deleted software"
    )
def software_delete(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    NAAN: str, 
    postfix: str
    ):
    """
    Deletes a software based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    softwareGUID = f"ark:{NAAN}/{postfix}"

    softwareInstance, deleteStatus = deleteSoftware(
            softwareGUID, 
            identifierCollection, 
            userCollection
            )

    if deleteStatus.success:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": softwareInstance.model_dump(
                    by_alias=True, 
                    include=['guid', 'name', 'description', 'metadataType', 'author']
                    )
                }
            )
    else:
        return JSONResponse(
            status_code=deleteStatus.status_code,
            content={"error": f"{str(deleteStatus.message)}"}
        )
