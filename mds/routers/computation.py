import pymongo
from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.dataset import Dataset
from mds.models.computation import Computation, list_computation
from mds.database.container_config import *
from mds.database.computation_config import *
from mds.database.config import *
from datetime import datetime
import time
import docker
import requests

from mds.utilities.operation_status import OperationStatus
from mds.utilities.funcs import *

router = APIRouter()


@router.post("/computation")
def computation_create(computation: Computation, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = computation.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": computation.id, "@type": "evi:Computation"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/computation")
def computation_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    computation = list_computation(mongo_collection)

    mongo_client.close()

    return computation


@router.get("/computation/ark:{NAAN}/{postfix}")
def computation_get(NAAN: str, postfix: str, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    computation_id = f"ark:{NAAN}/{postfix}"

    computation = Computation.construct(id=computation_id)

    read_status = computation.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return computation
    else:
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/computation")
def computation_update(computation: Computation, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = computation.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": computation.id, "@type": "evi:Computation"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/computation/ark:{NAAN}/{postfix}")
def computation_delete(NAAN: str, postfix: str):
    computation_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    computation = Computation.construct(id=computation_id)

    delete_status = computation.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": computation_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}


def run_custom_container(self, MongoClient: pymongo.MongoClient, compute_resources) -> OperationStatus:
    dateCreated = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")

    dataset_ids = compute_resources[DATASET_KEY]
    script_id = compute_resources[SCRIPT_KEY]

    usedDatasets = []
    usedSoftware = {}


    # Locate and download the dataset(s)
    if dataset_ids and isinstance(dataset_ids, list):
        for dataset_id in dataset_ids:
            r = requests.get(ROOT_URL + f"dataset/{dataset_id}")
            dataset_download_id, dataset_file_location, dataset_file_name = get_distribution_attr(dataset_id, r)

            # Download the content of the dataset
            data_download_dataset_download = requests.get(ROOT_URL + f"datadownload/{dataset_download_id}/download")
            dataset_content = data_download_dataset_download.content
            # print(dataset_content)

            with open('/home/sadnan/compute-test/data/' + dataset_file_name, 'wb') as binary_data_file:
                binary_data_file.write(dataset_content)

    if script_id:
        r = requests.get(ROOT_URL + f"software/{script_id}")
        script_download_id, script_file_location, script_file_name = get_distribution_attr(script_id, r)

        # Download the content of the script
        data_download_software_read = requests.get(ROOT_URL + f"datadownload/{script_download_id}/download")
        script_content = data_download_software_read.content


        with open('/home/sadnan/compute-test/' + script_file_name, 'wb') as binary_data_file:
            binary_data_file.write(script_content)

    client = docker.from_env()

    container = client.containers.run(
        image=IMAGE,
        command=COMMAND,
        auto_remove=True,
        working_dir=MOUNT_VOL,
        volumes={
            SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'},
            DATA_VOL: {'bind': MOUNT_DATA_VOL, 'mode': 'rw'},
            OUTPUT_VOL: {'bind': MOUNT_OUTPUT_VOL, 'mode': 'rw'},
        }
    )
    # output = to_str(container).attach(stdout=True, stream=True, logs=True)
    # for line in output:
    #    print(to_str(line))

    dateFinished = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")

    if container.decode('utf-8') == b'':
        return OperationStatus(False, f"error running the container", 400)

    # update computation with metadata
    with MongoClient.start_session(causal_consistency=True) as session:
        mongo_database = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]

        for dataset_id in dataset_ids:
            dataset_metadata = mongo_collection.find_one({"@id": dataset_id}, session=session)
            if dataset_metadata is None:
                return OperationStatus(False, f"dataset {dataset_id} not found", 404)

            dataset_compact = {
                "@id": dataset_metadata.get("@id"),
                "@type": dataset_metadata.get('@type'),
                "name": dataset_metadata.get('name')
            }
            usedDatasets.append(dataset_compact)

        script_metadata = mongo_collection.find_one({"@id": script_id}, session=session)
        if script_metadata == None:
            return OperationStatus(False, f"script {script_id} not found", 404)

        script_compact = {
            "@id": script_metadata.get("@id"),
            "@type": script_metadata.get('@type'),
            "name": script_metadata.get('name')
        }
        usedSoftware = script_compact

        update_computation_upon_execution = mongo_collection.update_one(
            {"@id": self.id},
            {"$set": {
                "dateCreated": dateCreated,
                "dateFinished": dateFinished,
                "usedSoftware": usedSoftware,
                "usedDataset": usedDatasets,
            }},
            session=session
        ),

    return OperationStatus(True, "", 201)
