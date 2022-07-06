from bson import SON
from pydantic import Extra
from typing import List, Union, Optional
from datetime import datetime
from pathlib import Path
from mds.database import mongo
from mds.models.fairscape_base import *
from mds.models.dataset import Dataset
from mds.models.download import Download as DataDownload
from mds.models.software import Software
from mds.models.compact.user import UserCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView
from mds.models.compact.organization import OrganizationCompactView
from mds.utilities.funcs import *
from mds.utilities.utils import *
import requests
import docker
import time
import uuid
import pathlib
import shutil
from mds.database.config import MINIO_BUCKET, MONGO_DATABASE, MONGO_COLLECTION
from mds.database.minio import *
from mds.database.container_config import *

root_url = "http://localhost:8000/"


class Computation(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "evi:Computation"
    owner: UserCompactView

    # author: str
    # dateCreated: datetime
    # dateFinished: datetime
    # associatedWith: List[Union[OrganizationCompactView, UserCompactView]]
    container: Optional[str]
    usedSoftware: str
    usedDataset: str
    containerId: Optional[str]

    class Config:
        extra = Extra.allow

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO initialize attributes of computation
        # self.author = ""
        # self.dateCreated = ""
        # self.dateFinished = ""
        # self.associatedWith = []
        # self.usedSoftware = ""
        # self.usedDataset = ""

        # check that computation does not already exist
        if MongoCollection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "computation already exists", 400)

        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner.id}) is None:
            return OperationStatus(False, "owner does not exist", 404)

        # embeded bson documents to enable Mongo queries
        computation_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        computation_dict["owner"] = SON([(key, value) for key, value in computation_dict["owner"].items()])

        # update operations for the owner user of the computation
        add_computation_update = {
            "$push": {"computations": SON([("@id", self.id), ("@type", "evi:Computation"), ("name", self.name)])}
        }

        computation_bulk_write = [
            pymongo.InsertOne(computation_dict),
            # update owner model to have listed the computation
            pymongo.UpdateOne({"@id": self.owner.id}, add_computation_update)
        ]

        # perform the bulk write
        try:
            bulk_write_result = MongoCollection.bulk_write(computation_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"error performing bulk write operations: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create computation error: {bulk_write_result.bulk_api_result}", 500)

        return OperationStatus(True, "", 201)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO e.g. when computation is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Delete the computation. Update each user who is an owner of the computation.

        Args:
            MongoCollection (pymongo.collection.Collection): _description_

        Returns:
            OperationStatus: _description_
        """

        # check that record exists
        # also, if successfull, will unpack the data we need to build the update operation
        read_status = self.read(MongoCollection)

        if not read_status.success:
            if read_status.status_code == 404:
                return OperationStatus(False, "computation not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"computations": {"@id": self.id}}}

        # for ever member, remove the computation from their list of computation
        # bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit = [
            pymongo.UpdateOne({"@id": self.owner.id}, pull_operation)
        ]

        # operations to delete the computation document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.id})
        )

        # run the transaction
        try:
            bulk_edit_result = MongoCollection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete Computation Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)

    def run_custom_container(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        mongo_db = MongoClient['test']
        mongo_collection = mongo_db['testcol']

        read_status = self.read(mongo_collection)
        if read_status.success != True:
            return read_status

        # dateCreated = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")
        #
        # dataset_ids = self.usedDataset
        # script_id = self.usedSoftware
        # container_image = self.container
        #
        # # find the locations of all the files
        # dataset_files = []
        # if isinstance(dataset_ids, list):
        #     for dataset_guid in dataset_ids:
        #         found_dataset = Dataset.construct(id=dataset_guid)
        #
        #         if found_dataset.read(mongo_collection).success != True:
        #             return OperationStatus(False, "", 400)
        #         print(found_dataset)
        #         dataset_files.append(found_dataset.distribution["contentUrl"])
        # else:
        #     dataset_guid = dataset_ids
        #     found_dataset = Dataset.construct(id=dataset_guid)
        #
        #     if found_dataset.read(mongo_collection).success != True:
        #         return OperationStatus(False, "", 400)
        #     print("outside", found_dataset)
        #     dataset_files.append(found_dataset.distribution["contentUrl"])
        # # find the software contentUrl
        # software = Software.construct(id=self.usedSoftware)
        # if software.read(mongo_collection).success != True:
        #     return OperationStatus(False, "", 400)
        #
        # # create a temporary folder for the data to transfered to the job
        #
        # # TODO create random_id for the job folder
        # p = pathlib.Path("/tmp/job_id").mkdir(parents=True, exist_ok=True)
        #
        # data_path = p + "/input/dataset"
        # software_path = p + "/input/software"
        # print(data_path, software_path)
        #
        # minio_client = GetMinioConfig()
        #
        # for dataset_path in dataset_files:
        #
        #     download_path = data_path + pathlib.Path(dataset_path).name
        #
        #     # use minio to transfer all datasetfiles
        #     download_object_metadata =minio_client.fget_object(
        #         MINIO_BUCKET,
        #         dataset_path,
        #         download_path
        #         )
        #
        #     # TODO determine minio download success
        #     # i.e. checking that the file is there and the same size
        #
        # # download the software to the temporary job folder
        #
        # software_download_path = software_path + pathlib.Path(software.contentUrl).name
        #
        # # use minio to transfer all datasetfiles
        # software_object_metadata =minio_client.fget_object(
        #     MINIO_BUCKET,
        #     software.contentUrl,
        #     software_download_path
        #     )

        # TODO determine software download success

        client = docker.from_env()
        container = client.containers.run(
            image=self.container,
            command=COMMAND,
            auto_remove=False,
            # detach=True required to get the Container object with attributes
            detach=True,
            working_dir=MOUNT_VOL,
            # any of the following three volumes mounting would work
            # volumes={SOURCE_VOL: {'bind': MOUNT_VOL}} # as a dict
            # volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'}} # as a dict
            # volumes=[SOURCE_VOL + ':' + MOUNT_VOL] # as a list
            volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'},
                     DATA_VOL: {'bind': MOUNT_DATA_VOL, 'mode': 'rw'},
                     OUTPUT_VOL: {'bind': MOUNT_OUTPUT_VOL, 'mode': 'rw'},
                     }
        )

        #
        # TODO Ensure successful launch of the container, exception handling
        #

        if container.id is None:
            return OperationStatus(False, f"error retrieving container id from launched container", 404)

        # assign long-form container id
        self.containerId = container.id

        # Update computation with info from the custom container
        session = MongoClient.start_session(causal_consistency=True)
        mongo_database = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]

        # update computation with the container id
        update_computation_result = mongo_collection.update_one(
            {"@id": self.id},
            {"$set": {
                "containerId": self.containerId
            }},
            session=session
        )

        if update_computation_result.matched_count != 1 and update_computation_result.modified_count != 1:
            return OperationStatus(False, f"error updating container id", 500)

        return OperationStatus(True, "", 201)


# def _run_container(self):
#         dataset_ids = []
#         script_id = ""
#         # Locate and download the dataset(s)
#         if dataset_ids and isinstance(dataset_ids, list):
#             for dataset_id in dataset_ids:
#                 r = requests.get(root_url + f"dataset/{dataset_id}")
#                 dataset_download_id, dataset_file_location, dataset_file_name = get_distribution_attr(dataset_id, r)
#                 print(dataset_download_id, dataset_file_location, dataset_file_name)
#
#                 # Download the content of the dataset
#                 data_download_dataset_download = requests.get(root_url + f"datadownload/{dataset_download_id}/download")
#                 dataset_content = data_download_dataset_download.content
#                 # print(dataset_content)
#
#                 with open('/home/sadnan/compute-test/data/' + dataset_file_name, 'wb') as binary_data_file:
#                     binary_data_file.write(dataset_content)
#
#         if script_id:
#             r = requests.get(root_url + f"software/{script_id}")
#             script_download_id, script_file_location, script_file_name = get_distribution_attr(script_id, r)
#             print(script_download_id, script_file_location, script_file_name)
#
#             # Download the content of the script
#             data_download_software_read = requests.get(root_url + f"datadownload/{script_download_id}/download")
#             script_content = data_download_software_read.content
#             # print(script_content)
#
#             with open('/home/sadnan/compute-test/' + script_file_name, 'wb') as binary_data_file:
#                 binary_data_file.write(script_content)
#
#         # select docker image
#         image_name = "python"
#         image_tag = "alpine"
#         IMAGE = f"{image_name}:{image_tag}"
#
#         # Volume mapping in the container
#         SOURCE_VOL = '/home/sadnan/compute-test'
#         MOUNT_VOL = '/cont/vol/script'
#
#         # script to run
#         SCRIPT_NAME = 'sum_script.py'
#
#         # command to run python script 'python3 /path/to/script/in/mounted/container/vol'
#         COMMAND = ['python', f'{MOUNT_VOL}/{SCRIPT_NAME}']
#
#         CONTAINER_NAME = "compute-service-custom-container"
#
#         client = docker.from_env()
#
#         container = client.containers.run(
#             image=IMAGE,
#             command=COMMAND,
#             auto_remove=True,
#             working_dir=MOUNT_VOL,
#             # any of the following three volumes mounting would work
#             # volumes={SOURCE_VOL: {'bind': MOUNT_VOL}} # as a dict
#             # volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'}} # as a dict
#             # volumes=[SOURCE_VOL + ':' + MOUNT_VOL] # as a list
#             volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'},
#                      '/home/sadnan/compute-test/data': {'bind': '/cont/vol/script/data', 'mode': 'rw'},
#                      '/home/sadnan/compute-test/outputs': {'bind': '/cont/vol/script/outputs', 'mode': 'rw'},
#                      }
#         )
#         # output = to_str(container).attach(stdout=True, stream=True, logs=True)
#         # for line in output:
#         #    print(to_str(line))
#
#         dateFinished = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")
#         # self.dateFinished = dateFinished
#
#         # print("time lapsed: ", dateCreated, dateFinished)
#
#         if container.decode('utf-8') == b'':
#             return OperationStatus(False, f"error running the container", 400)
#
#         # print(container)
#
#         # update computation with metadata
#         with MongoClient.start_session(causal_consistency=True) as session:
#             mongo_database = MongoClient[MONGO_DATABASE]
#             mongo_collection = mongo_database[MONGO_COLLECTION]
#
#             for dataset_id in dataset_ids:
#                 dataset_metadata = mongo_collection.find_one({"@id": dataset_id}, session=session)
#                 if dataset_metadata == None:
#                     return OperationStatus(False, f"dataset {dataset_id} not found", 404)
#
#                 dataset = Dataset.construct(**dataset_metadata)
#                 # update the encodesCreativeWork property with a DatasetCompactView
#                 dataset_compact = {
#                     "@id": dataset_metadata.get("@id"),
#                     "@type": dataset_metadata.get('@type'),
#                     "name": dataset_metadata.get('name')
#                 }
#                 usedDatasets.append(dataset_compact)
#
#             script_metadata = mongo_collection.find_one({"@id": script_id}, session=session)
#             if script_metadata == None:
#                 return OperationStatus(False, f"script {script_id} not found", 404)
#
#             script = Dataset.construct(**dataset_metadata)
#             # update the encodesCreativeWork property with a DatasetCompactView
#             script_compact = {
#                 "@id": script_metadata.get("@id"),
#                 "@type": script_metadata.get('@type'),
#                 "name": script_metadata.get('name')
#             }
#             usedSoftware = script_compact
#
#             # print(usedDatasets, usedSoftware, dateCreated, dateFinished)
#
#             update_computation_upon_execution = mongo_collection.update_one(
#                 {"@id": self.id},
#                 {"$set": {
#                     "dateCreated": dateCreated,
#                     "dateFinished": dateFinished,
#                     "usedSoftware": usedSoftware,
#                     "usedDataset": usedDatasets,
#                 }},
#                 session=session
#             ),
#
#         return OperationStatus(True, "", 201)


def list_computation(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Computation"},
        projection={"_id": False}
    )
    return {
        "computations": [{"@id": computation.get("@id"), "@type": "evi:Computation", "name": computation.get("name")}
                         for computation in cursor]}


def RegisterComputation(computation: Computation):
    """
    Given a computation ID first await the success or failure of the container in the ongoing computation.
    If successfull register all datasets in the output folder for the supplied computation, 
    and append the computation metadata with status of the containers execution and logs if applicable
    """

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    minio_client = GetMinioConfig()

    if computation.containerId == "":
        write_container_log(f"error: containerId does not exist")

    client = docker.from_env()

    # stores the container state  in a dict
    container_state = {}

    # keeps track of the 'Running = True/False' state
    is_container_running = True

    while is_container_running:
        try:
            container = client.containers.get(container_id=computation.containerId)
            container_state = container.attrs["State"]
            is_container_running = container_state["Running"]
        except docker.errors.NotFound as nfe:
            write_container_log(f"error: unable to retrieve container with {computation.containerId} : {nfe}")

        print(container_state)
        write_container_log(json.dumps(container_state))
        # delay 1 sec
        time.sleep(1)

    status = container_state["Status"]
    exit_code = container_state["ExitCode"]
    date_created = container_state["StartedAt"]
    date_finished = container_state["FinishedAt"]

    # container exited gracefully
    if status == "exited" and exit_code == 0:
        generates = []
        # get all output files
        for output_file in Path(COMPUTATION_OUTPUT_DIR).rglob('*'):
            if output_file.is_file():
                print(output_file.name)
                file_parent = output_file.parent
                file_name = output_file.name
                file_name_prefix = output_file.stem
                file_extension = ''.join(output_file.suffixes)  # includes .tar.gz
                dataset = Dataset(**{
                    "@id": f"ark:99999/{str(uuid.uuid4())}",
                    "@type": "evi:Dataset",
                    # TODO find the best way to represent name as it represents the directory in MINio
                    "name": f"output-{file_name_prefix}",
                    "owner": computation.owner,
                    "generatedBy": computation.id
                })

                create_status = dataset.create(mongo_client)

                if create_status.success:
                    generates.append({"@id": dataset.id, "@type": dataset.type, "name": dataset.name})

                data_download = DataDownload(**{
                    "@id": f"ark:99999/{str(uuid.uuid4())}",
                    "@type": "DataDownload",
                    "name": file_name,
                    "encodingFormat": file_extension,
                    "encodesCreativeWork": dataset.id
                })

                create_status = data_download.create_metadata(mongo_client)
                print(create_status)

                # with open(output_file, "rb") as output_file_object:
                #     upload_status = data_download.register(output_file_object, mongo_collection, minio_client)
                #     if upload_status.success != True:
                #         return JSONResponse(
                #             status_code=500,
                #             content={"error": f"unable to upload object: {output_file}"}
                #         )

        # Update computation with info from the custom container
        session = mongo_client.start_session(causal_consistency=True)

        mongo_database = mongo_client[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]

        container = client.containers.get(container_id=computation.containerId)
        logs = container.logs()
        print(logs)

        # update computation with the container-start and end time
        update_computation_result = mongo_collection.update_one(
            {"@id": computation.id},
            {"$set": {
                "dateCreated": date_created,
                "dateFinished": date_finished,
                "generates": generates,
                "logs": to_str(logs)
            }},
            session=session
        )

        if update_computation_result.matched_count != 1 and update_computation_result.modified_count != 1:
            write_container_log(f"error: unable to update container id")

    else:
        write_container_log(f"error: container exited unexpectedly")

    # remove the container
    container.remove()
    write_container_log(f"message: container {computation.containerId} removed successfully")

    # clean up files
    dir_to_clean = pathlib.Path(COMPUTATION_OUTPUT_DIR)
    write_container_log(f"message: cleaning output directory: {dir_to_clean}")
    if dir_to_clean.exists() and dir_to_clean.is_dir():
        shutil.rmtree(dir_to_clean)
        write_container_log(f"message: output directory: {dir_to_clean} removed successfully")
    else:
        write_container_log(f"message: error removing output directory: {dir_to_clean}")
    print('Run Custom Container: All done')

