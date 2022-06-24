from fastapi import APIRouter
from fastapi.responses import JSONResponse

from mds.database import mongo
from mds.models.dataset import Dataset, list_dataset

router = APIRouter()


@router.post("/dataset")
def dataset_create(dataset: Dataset):
    mongo_client = mongo.GetConfig()

    create_status = dataset.create(mongo_collection, mongo_client)

    mongo_client.close()

    if create_status.success:
        return JSONResponse(
            status_code = 201,
            content={"created": {"@id": dataset.id, "@type": "evi:Dataset"}}
        )
    else:
        return JSONResponse(
            status_code = create_status.status_code,
            content = {"error": create_status.message}
        )


@router.get("/dataset")
def dataset_list():
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    dataset = list_dataset(mongo_collection)

    mongo_client.close()

    return dataset


@router.get("/dataset/ark:{NAAN}/{postfix}")
def dataset_get(NAAN: str, postfix: str):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    dataset_id = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(id=dataset_id)

    read_status = dataset.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return dataset
    else:
        return JSONResponse(
            status_code = read_status.status_code,
            content= {"error": read_status.message}
        )


@router.put("/dataset")
def dataset_update(dataset: Dataset):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = dataset.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code = 200,
            content= {"updated": {"@id": dataset.id, "@type": "evi:Dataset"}}
        )
    else:
        return JSONResponse(
            status_code = update_status.status_code,
            content= {"error": update_status.message}
        )


@router.delete("/dataset/ark:{NAAN}/{postfix}")
def dataset_delete(NAAN: str, postfix: str):
    dataset_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    dataset = Dataset.construct(id=dataset_id)

    delete_status = dataset.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code = 200,
            content= {"deleted": {"@id": dataset_id}}
        )

    else:
        return JSONResponse( 
            status_code = delete_status.status_code,
            content= {"error": f"{str(delete_status.message)}"}
        )
