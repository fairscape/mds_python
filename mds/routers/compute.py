from fastapi import APIRouter
from fastapi.responses import JSONResponse

from mds.database import mongo, minio
from mds.models.dataset import Dataset
from mds.models.computation import Computation
from mds.models.software import Software
import json
from mds.utilities.funcs import parse_request


router = APIRouter()


@router.post("/compute/ark:{NAAN}/{computation_id}")
def run_computation(NAAN: str, computation_id: str, body: dict):
    compute_resources = body

    computation_id = f"ark:{NAAN}/{computation_id}"

    computation = Computation.construct(id=computation_id)

    # get the connection to the databases
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    minio_client = minio.GetMinioConfig()

    # check if computation id exists
    computation_read_status = computation.read(mongo_collection)

    # if the metadata wasn't found successfully handle errors
    if computation_read_status.success != True:

        if computation_read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": computation.id,
                    "error": "computation not found"
                })

        else:
            return JSONResponse(
                status_code=computation_read_status.status_code,
                content={
                    "@id": computation.id,
                    "error": computation_read_status.message
                })

    # get_computation = requests.get(ROOT_URL + f"computation/{computation_id}")

    is_correct_input, dataset_ids, script_id, error_msg = parse_request(json.dumps(compute_resources))
    # print(is_correct_input, dataset_ids, script_id, error_msg)
    if not is_correct_input:
        return JSONResponse(
            status_code=400,
            content={
                "error": error_msg
            })

    if isinstance(dataset_ids, list):
        if len(dataset_ids) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing dataset identifier(s)"
                })
    elif not dataset_ids:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing dataset identifier(s)"
            })
    if not script_id:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing script identifier"
            })

    if not isinstance(dataset_ids, list):
        dataset_ids = [dataset_ids]

    for dataset_id in dataset_ids:
        # check if the dataset id exists
        dataset = Dataset.construct(id=dataset_id)
        dataset_read_status = dataset.read(mongo_collection)

        # if the metadata wasn't found successfully handle errors
        if dataset_read_status.success != True:

            if dataset_read_status.status_code == 404:
                return JSONResponse(
                    status_code=404,
                    content={
                        "@id": dataset.id,
                        "error": "dataset not found"
                    })

            else:
                return JSONResponse(
                    status_code=dataset_read_status.status_code,
                    content={
                        "@id": dataset.id,
                        "error": dataset_read_status.message
                    })

    # check if the script id exists
    software = Software.construct(id=script_id)
    script_read_status = software.read(mongo_collection)

    # if the metadata wasn't found successfully handle errors
    if script_read_status.success != True:
        if script_read_status.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "@id": software.id,
                    "error": "software not found"
                })

        else:
            return JSONResponse(
                status_code=script_read_status.status_code,
                content={
                    "@id": software.id,
                    "error": script_read_status.message
                })

    container_run_status = computation.run_custom_container(mongo_client, compute_resources)

    if container_run_status.success != True:
        return JSONResponse(
            status_code=container_run_status.status_code,
            content={
                "@id": computation.id,
                "error": container_run_status.message
            })

    return {
        "status": "Success",
        "data": compute_resources,
        "comp_id": computation
    }











