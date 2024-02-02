import pymongo
from fastapi import APIRouter, Response, BackgroundTasks
from fairscape_mds.mds.config import (
    get_minio_config,
    get_casbin_config,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
    CasbinConfig
) 

from fairscape_mds.mds.compute import create_job
from fairscape_mds.mds.models.computation import Computation, list_computation, RegisterComputation
from fairscape_mds.mds.database.container_config import *
from fairscape_mds.mds.database.config import *
from datetime import datetime
import time
import docker


from mds.utilities.operation_status import OperationStatus
from mds.utilities.funcs import *

router = APIRouter()

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

casbin_enforcer = get_casbin_enforcer()
casbin_enforcer.load_policy()

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
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    create_status = computation.create(mongo_collection)

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": computation.id, "@type": "evi:Computation"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.put("/computation/execute/ark:{NAAN}/{postfix}")
def computation_execute(NAAN: str, postfix: str):

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    computation_id = f"ark:{NAAN}/{postfix}"

    computation = Computation.construct(id=computation_id)
    read_status = computation.read(mongo_collection)
    
    if read_status.success != True: 
        mongo_client.close()
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
            )

    res = create_job(computation_id)
 
    return JSONResponse(
            status_code=201,
            content={"message": "launched kubernetes job"}
        )


@router.get("/computation",
            summary="List all computations",
            response_description="Retrieved list of computations")
def computation_list(response: Response):
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    computation = list_computation(mongo_collection)

    mongo_client.close()

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
    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    computation_id = f"ark:{NAAN}/{postfix}"

    computation = Computation.construct(id=computation_id)

    read_status = computation.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return computation
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


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

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]
    computation_id = f"ark:{NAAN}/{postfix}"

    computation = Computation.construct(id=computation_id)

    delete_status = computation.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": computation_id, "@type": "evi:Computation", "name": computation.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )


# def run_custom_container(self, MongoClient: pymongo.MongoClient, compute_resources) -> OperationStatus:
#     dateCreated = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")
#
#     dataset_ids = compute_resources[DATASET_KEY]
#     script_id = compute_resources[SCRIPT_KEY]
#
#     usedDatasets = []
#     usedSoftware = {}
#
#     # Locate and download the dataset(s)
#     if dataset_ids and isinstance(dataset_ids, list):
#         for dataset_id in dataset_ids:
#             r = requests.get(ROOT_URL + f"dataset/{dataset_id}")
#             dataset_download_id, dataset_file_location, dataset_file_name = get_distribution_attr(dataset_id, r)
#
#             # Download the content of the dataset
#             data_download_dataset_download = requests.get(ROOT_URL + f"datadownload/{dataset_download_id}/download")
#             dataset_content = data_download_dataset_download.content
#             # print(dataset_content)
#
#             with open('/home/sadnan/compute-test/data/' + dataset_file_name, 'wb') as binary_data_file:
#                 binary_data_file.write(dataset_content)
#
#     if script_id:
#         r = requests.get(ROOT_URL + f"software/{script_id}")
#         script_download_id, script_file_location, script_file_name = get_distribution_attr(script_id, r)
#
#         # Download the content of the script
#         data_download_software_read = requests.get(ROOT_URL + f"datadownload/{script_download_id}/download")
#         script_content = data_download_software_read.content
#
#         with open('/home/sadnan/compute-test/' + script_file_name, 'wb') as binary_data_file:
#             binary_data_file.write(script_content)
#
#     client = docker.from_env()
#
#     container = client.containers.run(
#         image=IMAGE,
#         command=COMMAND,
#         auto_remove=True,
#         working_dir=MOUNT_VOL,
#         volumes={
#             SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'},
#             DATA_VOL: {'bind': MOUNT_DATA_VOL, 'mode': 'rw'},
#             OUTPUT_VOL: {'bind': MOUNT_OUTPUT_VOL, 'mode': 'rw'},
#         }
#     )
#     # output = to_str(container).attach(stdout=True, stream=True, logs=True)
#     # for line in output:
#     #    print(to_str(line))
#
#     dateFinished = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")
#
#     if container.decode('utf-8') == b'':
#         return OperationStatus(False, f"error running the container", 400)
#
#     # update computation with metadata
#     with MongoClient.start_session(causal_consistency=True) as session:
#         mongo_database = MongoClient[MONGO_DATABASE]
#         mongo_collection = mongo_database[MONGO_COLLECTION]
#
#         for dataset_id in dataset_ids:
#             dataset_metadata = mongo_collection.find_one({"@id": dataset_id}, session=session)
#             if dataset_metadata is None:
#                 return OperationStatus(False, f"dataset {dataset_id} not found", 404)
#
#             dataset_compact = {
#                 "@id": dataset_metadata.get("@id"),
#                 "@type": dataset_metadata.get('@type'),
#                 "name": dataset_metadata.get('name')
#             }
#             usedDatasets.append(dataset_compact)
#
#         script_metadata = mongo_collection.find_one({"@id": script_id}, session=session)
#         if script_metadata == None:
#             return OperationStatus(False, f"script {script_id} not found", 404)
#
#         script_compact = {
#             "@id": script_metadata.get("@id"),
#             "@type": script_metadata.get('@type'),
#             "name": script_metadata.get('name')
#         }
#         usedSoftware = script_compact
#
#         update_computation_upon_execution = mongo_collection.update_one(
#             {"@id": self.id},
#             {"$set": {
#                 "dateCreated": dateCreated,
#                 "dateFinished": dateFinished,
#                 "usedSoftware": usedSoftware,
#                 "usedDataset": usedDatasets,
#             }},
#             session=session
#         ),
#
#     return OperationStatus(True, "", 201)
