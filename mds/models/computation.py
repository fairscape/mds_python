from bson import SON
from pydantic import Extra
from typing import List, Union
from datetime import datetime
from mds.models.fairscape_base import *
from mds.models.dataset import Dataset
from mds.models.compact.user import UserCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView
from mds.models.compact.organization import OrganizationCompactView
from mds.utilities.funcs import *
import requests
import docker
import time
from mds.database.config import MINIO_BUCKET, MONGO_DATABASE, MONGO_COLLECTION

root_url = "http://localhost:8000/"

class Computation(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "evi:Computation"
    owner: UserCompactView

    # author: str
    # dateCreated: datetime
    # dateFinished: datetime
    # associatedWith: List[Union[OrganizationCompactView, UserCompactView]]
    # usedSoftware: SoftwareCompactView
    # usedDataset: DatasetCompactView

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

    def run_custom_container(self, MongoClient: pymongo.MongoClient, compute_resources) -> OperationStatus:

        dateCreated = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")

        dataset_ids = compute_resources["datasetID"]
        script_id = compute_resources["scriptID"]

        usedDatasets = []
        usedSoftware = ""
        dateCreated

        # Locate and download the dataset(s)
        if dataset_ids and isinstance(dataset_ids, list):
            for dataset_id in dataset_ids:
                r = requests.get(root_url + f"dataset/{dataset_id}")
                dataset_download_id, dataset_file_location, dataset_file_name = get_distribution_attr(dataset_id, r)
                print(dataset_download_id, dataset_file_location, dataset_file_name)

                # Download the content of the dataset
                data_download_dataset_download = requests.get(root_url + f"datadownload/{dataset_download_id}/download")
                dataset_content = data_download_dataset_download.content
                # print(dataset_content)

                with open('/home/sadnan/compute-test/data/' + dataset_file_name, 'wb') as binary_data_file:
                    binary_data_file.write(dataset_content)

        if script_id:
            r = requests.get(root_url + f"software/{script_id}")
            script_download_id, script_file_location, script_file_name = get_distribution_attr(script_id, r)
            print(script_download_id, script_file_location, script_file_name)

            # Download the content of the script
            data_download_software_read = requests.get(root_url + f"datadownload/{script_download_id}/download")
            script_content = data_download_software_read.content
            # print(script_content)

            with open('/home/sadnan/compute-test/' + script_file_name, 'wb') as binary_data_file:
                binary_data_file.write(script_content)

        # select docker image
        image_name = "python"
        image_tag = "alpine"
        IMAGE = f"{image_name}:{image_tag}"

        # Volume mapping in the container
        SOURCE_VOL = '/home/sadnan/compute-test'
        MOUNT_VOL = '/cont/vol/script'

        # script to run
        SCRIPT_NAME = 'sum_script.py'

        # command to run python script 'python3 /path/to/script/in/mounted/container/vol'
        COMMAND = ['python', f'{MOUNT_VOL}/{SCRIPT_NAME}']

        CONTAINER_NAME = "compute-service-custom-container"

        client = docker.from_env()

        container = client.containers.run(
            image=IMAGE,
            command=COMMAND,
            auto_remove=True,
            working_dir=MOUNT_VOL,
            # any of the following three volumes mounting would work
            # volumes={SOURCE_VOL: {'bind': MOUNT_VOL}} # as a dict
            # volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'}} # as a dict
            # volumes=[SOURCE_VOL + ':' + MOUNT_VOL] # as a list
            volumes={SOURCE_VOL: {'bind': MOUNT_VOL, 'mode': 'rw'},
                     '/home/sadnan/compute-test/data': {'bind': '/cont/vol/script/data', 'mode': 'rw'},
                     '/home/sadnan/compute-test/outputs': {'bind': '/cont/vol/script/outputs', 'mode': 'rw'},
                     }
        )
        # output = to_str(container).attach(stdout=True, stream=True, logs=True)
        # for line in output:
        #    print(to_str(line))

        dateFinished = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")
        # self.dateFinished = dateFinished

        # print("time lapsed: ", dateCreated, dateFinished)

        if container.decode('utf-8') == b'':
            return OperationStatus(False, f"error running the container", 400)

        # print(container)

        # update computation with metadata
        with MongoClient.start_session(causal_consistency=True) as session:
            mongo_database = MongoClient[MONGO_DATABASE]
            mongo_collection = mongo_database[MONGO_COLLECTION]

            for dataset_id in dataset_ids:
                dataset_metadata = mongo_collection.find_one({"@id": dataset_id}, session=session)
                if dataset_metadata == None:
                    return OperationStatus(False, f"dataset {dataset_id} not found", 404)

                dataset = Dataset.construct(**dataset_metadata)
                # update the encodesCreativeWork property with a DatasetCompactView
                dataset_compact = {
                    "@id": dataset_metadata.get("@id"),
                    "@type": dataset_metadata.get('@type'),
                    "name": dataset_metadata.get('name')
                }
                usedDatasets.append(dataset_compact)

            script_metadata = mongo_collection.find_one({"@id": script_id}, session=session)
            if script_metadata == None:
                return OperationStatus(False, f"script {script_id} not found", 404)

            script = Dataset.construct(**dataset_metadata)
            # update the encodesCreativeWork property with a DatasetCompactView
            script_compact = {
                "@id": script_metadata.get("@id"),
                "@type": script_metadata.get('@type'),
                "name": script_metadata.get('name')
            }
            usedSoftware = script_compact

            # print(usedDatasets, usedSoftware, dateCreated, dateFinished)

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


def list_computation(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Computation"},
        projection={"_id": False}
    )
    return {
        "computations": [{"@id": computation.get("@id"), "@type": "evi:Computation", "name": computation.get("name")}
                         for computation in cursor]}

