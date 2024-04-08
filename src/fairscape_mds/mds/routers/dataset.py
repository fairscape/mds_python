from fastapi import APIRouter
from fastapi.responses import JSONResponse

from fairscape_mds.mds.config import (
    get_minio_config,
    get_mongo_config,
    get_mongo_client,
) 

from fairscape_mds.mds.models.dataset import Dataset, listDatasets

router = APIRouter()
mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

mongo_db = mongo_client[mongo_config.db]
identifier_collection = mongo_db[mongo_config.identifier_collection]
user_collection = mongo_db[mongo_config.user_collection]


@router.post("/dataset",
             summary="Create a dataset",
             response_description="The created dataset")
def dataset_create(dataset: Dataset):
    """
    Create a dataset with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Dataset
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """

    
    create_status = dataset.create(
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
def dataset_list():
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

    dataset_id = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(guid=dataset_id)

    read_status = dataset.read(identifier_collection)

    if read_status.success:
        return dataset
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )


@router.put("/dataset",
            summary="Update a dataset",
            response_description="The updated dataset")
def dataset_update(dataset: Dataset):
    update_status = dataset.update(identifier_collection)

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": dataset.id, "@type": "evi:Dataset"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/dataset/ark:{NAAN}/{postfix}",
               summary="Delete a dataset",
               response_description="The deleted dataset")
def dataset_delete(NAAN: str, postfix: str):
    """
    Deletes a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    dataset_id = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(guid=dataset_id)

    delete_status = dataset.delete(
            identifier_collection,
            user_collection
            )

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": dataset_id, "@type": "evi:Dataset", "name": dataset.name}}
        )

    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
