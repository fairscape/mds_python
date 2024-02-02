from fastapi import APIRouter
from fastapi.responses import JSONResponse

from fairscape_mds.mds.config import (
    get_minio_config,
    get_casbin_config,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
) 

from fairscape_mds.mds.database import mongo
from fairscape_mds.mds.models.dataset import Dataset
from fairscape_mds.mds.models.utils import list_dataset

router = APIRouter()
mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

casbin_enforcer = get_casbin_enforcer()
casbin_enforcer.load_policy()


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
    mongo_client = mongo.GetConfig()
    create_status = dataset.create(mongo_client)

    mongo_client.close()

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": dataset.id, "@type": "evi:Dataset"}}
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
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    dataset = list_dataset(mongo_collection)

    mongo_client.close()

    return dataset


@router.get("/dataset/ark:{NAAN}/{postfix}",
            summary="Retrieve a dataset",
            response_description="The retrieved dataset")
def dataset_get(NAAN: str, postfix: str):
    """
    Retrieves a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    dataset_id = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(id=dataset_id)

    read_status = dataset.read(mongo_collection)

    mongo_client.close()

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
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    update_status = dataset.update(mongo_collection)

    mongo_client.close()

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

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    dataset = Dataset.construct(id=dataset_id)

    delete_status = dataset.delete(mongo_collection)

    mongo_client.close()

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
