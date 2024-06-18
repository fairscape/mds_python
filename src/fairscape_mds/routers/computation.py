import pymongo
from fastapi import APIRouter, Response, BackgroundTasks
from fairscape_mds.config import (
    get_fairscape_config,
) 

from fairscape_mds.models.computation import (
        Computation,
        createComputation,
        listComputation,
        getComputation,
        updateComputation,
        deleteComputation
        )
from fairscape_mds.utilities.operation_status import OperationStatus
from fairscape_mds.utilities.funcs import *
from datetime import datetime
import time



router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_config = fairscapeConfig.mongo
mongo_client = fairscapeConfig.CreateMongoClient()

mongo_db = mongo_client[mongo_config.db]
identifierCollection = mongo_db[mongo_config.identifier_collection]
userCollection = mongo_db[mongo_config.user_collection]


@router.post("/computation",
             summary="Create a computation",
             response_description="The created computation")
def computation_create(computation: Computation, response: Response):
    """
    Create a computation with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Computation
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """

    createStatus = createComputation(computation, identifierCollection, userCollection)

    if createStatus.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": computation.guid, "@type": "evi:Computation", "name": computation.name}}
        )
    else:
        return JSONResponse(
            status_code=createStatus.status_code,
            content={"error": createStatus.message}
        )


@router.get("/computation",
            summary="List all computations",
            response_description="Retrieved list of computations")
def computation_list(response: Response):

    computation = listComputation(identifierCollection)
    return computation


@router.get("/computation/ark:{NAAN}/{postfix}",
            summary="Retrieve a computation",
            response_description="The retrieved computation")
def computation_get(NAAN: str, postfix: str, response: Response):
    """
    Retrieves a computation based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    computationGUID = f"ark:{NAAN}/{postfix}"

    computation, read_status = getComputation(computationGUID, identifierCollection)

    if read_status.success:
        return computation
    else:
        return JSONResponse(
                status_code=read_status.status_code,
                content={"error": read_status.message}
                )


@router.put("/computation",
            summary="Update a computation",
            response_description="The updated computation")
def computation_update(computation: Computation, response: Response):
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    computation_id = f"ark:{NAAN}/{postfix}"

    update_status = computation.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": computation.id, "@type": "evi:Computation"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/computation/ark:{NAAN}/{postfix}",
               summary="Delete a computation",
               response_description="The deleted computation")
def computation_delete(NAAN: str, postfix: str):
    """
    Deletes a computation based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    computationGUID = f"ark:{NAAN}/{postfix}"

    computationInstance, deleteStatus = deleteComputation(computationGUID, identifierCollection, userCollection)

    if deleteStatus.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": computationInstance.model_dump(by_alias=True)}
        )
    else:
        return JSONResponse(
            status_code=deleteStatus.status_code,
            content={"error": f"{str(deleteStatus.message)}"}
        )

