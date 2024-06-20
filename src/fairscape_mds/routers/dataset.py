from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from fairscape_mds.config import (
        get_fairscape_config
) 

from fairscape_mds.models.dataset import (
    DatasetCreateModel, 
    DatasetWriteModel,
    DatasetUpdateModel,
    listDatasets, 
    deleteDataset, 
    createDataset, 
)

from typing import Annotated
from fairscape_mds.models.user import User
from fairscape_mds.auth.oauth import getCurrentUser

router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_config = fairscapeConfig.mongo
mongo_client = fairscapeConfig.CreateMongoClient()

mongo_db = mongo_client[mongo_config.db]
identifier_collection = mongo_db[mongo_config.identifier_collection]
user_collection = mongo_db[mongo_config.user_collection]


@router.post("/dataset",
             summary="Create a dataset",
             response_description="The created dataset")
def dataset_create(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    dataset: DatasetCreateModel
    ):
    """
    Create a dataset with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Dataset
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """

    datasetInstance = convertDatasetCreateToWrite(datasetInstance, currentUser.guid)
    
    create_status = createDataset(
            currentUser,
            datasetInstance,
            identifier_collection,
            user_collection
            )

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": dataset.guid, "@type": "evi:Dataset", "name": dataset.name}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/dataset",
            summary="List all datasets",
            response_description="Retrieved list of datasets")
def dataset_list(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    ):
    datasets = listDatasets(identifier_collection)
    return datasets


@router.get("/dataset/ark:{NAAN}/{postfix}",
            summary="Retrieve a dataset",
            response_description="The retrieved dataset")
def dataset_get(NAAN: str, postfix: str):
    """
    Retrieves a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    datasetGUID = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(guid=datasetGUID)
    read_status = dataset.read(identifier_collection)

    if read_status.success:
        return dataset
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )


@router.put("/dataset/ark:{NAAN}/{postfix}",
            summary="Update a dataset",
            response_description="The updated dataset")
def dataset_update(
    NAAN: str,
    postfix: str,
    datasetUpdateInstance: DatasetUpdateModel,
    currentUser: Annotated[User, Depends(getCurrentUser)],
    ):

    datasetGUID = f"ark:{NAAN}/{postfix}"

    updateStatus = updateDataset(currentUser, datasetGUID, datasetUpdateInstance, identifier_collection)


    if updateStatus.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": dataset.id, "@type": "evi:Dataset"}}
        )
    else:
        return JSONResponse(
            status_code=updateStatus.status_code,
            content={"error": updateStatus.message}
        )


@router.delete("/dataset/ark:{NAAN}/{postfix}",
    summary="Delete a dataset",
    response_description="The deleted dataset")
def dataset_delete(
    currentUser: Annotated[User, Depends(getCurrentUser)],
    NAAN: str, 
    postfix: str
    ):
    """
    Deletes a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    datasetGUID = f"ark:{NAAN}/{postfix}"

    datasetMetadata, deleteStatus = deleteDataset(
            datasetGUID,
            identifier_collection,
            user_collection
            )

    if deleteStatus.success:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": datasetMetadata.model_dump(by_alias=True, include=['guid', 'name', 'description', 'metadataType'])
                }
        )

    else:
        return JSONResponse(
            status_code=deleteStatus.status_code,
            content={"error": f"{str(deleteStatus.message)}"}
        )
