from bson import SON
from pydantic import Extra
from typing import List, Union, Optional, Literal
from datetime import datetime
from pathlib import Path
from fairscape_mds.mds.models.fairscape_base import *
from fairscape_mds.mds.models.dataset import Dataset
from fairscape_mds.mds.models.download import Download as DataDownload
from fairscape_mds.mds.models.software import Software
from fairscape_mds.mds.models.fairscape_base import *
from fairscape_mds.mds.utilities.funcs import *
from fairscape_mds.mds.utilities.utils import *

from pydantic import BaseModel
import requests
import docker
import time
import uuid
import pathlib
import shutil

root_url = "http://localhost:8000/"
default_context = {
    "@vocab": "https://schema.org/", 
    "evi": "https://w3id.org/EVI#"
}


class Computation(FairscapeEVIBaseModel, extra = Extra.allow):
    metadataType: Literal['evi:Computation'] = Field(alias="@type")
    url: str
    owner: str
    author: str
    dateCreated: Optional[datetime] = Field(default=None)
    dateFinished: Optional[datetime] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    includedInDataCatalog: Optional[str] = Field(default=None)
    command: Optional[Union[str,List[str]]] = Field(default=None)
    usedSoftware: str
    usedDataset: List[str]
    generated: List[str]

def createComputation(
        computationInstance: Computation, 
        identifierCollection: pymongo.collection.Collection,
        userCollection: pymongo.collection.Collection
        ) -> OperationStatus:
    ''' create a Computation and Link all related entities
    '''

    # check that computation does not already exist
    if identifierCollection.find_one({"@id": computationInstance.guid}) is not None:
        return OperationStatus(False, "computation already exists", 400)

        # check that owner exists
    if userCollection.find_one({"@id": computationInstance.owner}) is None:
        return OperationStatus(False, f"owner {computationInstance.owner} does not exist", 404)


    # check that software exists
    if identifierCollection.find_one({"@id": computationInstance.usedSoftware}) is None:
        return OperationStatus(False, f"software {computationInstance.usedSoftware} does not exist", 404)

    # check that dataset exists
    for dataset in computationInstance.usedDataset:
        if identifierCollection.find_one({"@id": dataset}) is None:
            return OperationStatus(False, f"dataset {dataset} does not exist", 404)

    # check that generated exists
    for generated in computationInstance.generated:
        if identifierCollection.find_one({"@id": generated}) is None:
            return OperationStatus(False, f"generated dataset {dataset} does not exist", 404)

    # insert computation
    computationMetadata = computationInstance.model_dump(by_alias=True)
    insertComputationResult = identifierCollection.insert_one(computationMetadata)

    # update user
    updateUserResult = userCollection.update_one(
            {"@id": computationInstance.owner},
            {"$push": {"computations": computationInstance.guid}}
            )

    if updateUserResult.modified_count != 1:
        return OperationStatus(False, f"failed to update user list of software", 500)

    # update software
    updateSoftwareResult = identifierCollection.update_one(
            {"@id": computationInstance.usedSoftware},
            {"$push": {"usedBy": computationInstance.guid}}
            )

    if updateSoftwareResult.modified_count != 1:
        return OperationStatus(False, f"failed to update software with inverse property usedBy", 500)

    # update each usedDataset if in collection
    updateDatasetResult = identifierCollection.update_many(
            {"@id": {"$in": computationInstance.usedDataset}},
            {"$push": {"usedBy": computationInstance.guid}}
            )

    if updateDatasetResult.modified_count != len(computationInstance.usedDataset):
        # find which datasets were matched
        return OperationStatus(False, f"failed to update usedDataset with inverse property usedBy", 500)


    # update generated
    updateGeneratedResult = identifierCollection.update_many(
            {"@id": {"$in": computationInstance.generated}},
            {"$push": {"generatedBy": computationInstance.guid}}
            )

    if updateGeneratedResult.modified_count != len(computationInstance.generated):
        # find which datasets were matched
        return OperationStatus(False, f"failed to update generated Datasets with inverse property generatedBy", 500)


    return OperationStatus(True, "", 201)


def listComputation(identifierCollection: pymongo.collection.Collection):
    ''' List all computations
    '''

    cursor = identifierCollection.find(
        {"@type": "evi:Computation"},
        projection={"_id": False}
    )
    computationList = [ 
        {
            "@id": computation.get("@id"), 
            "@type": "evi:Computation", 
            "name": computation.get("name")
        } for computation in cursor
    ]

    return { "computations": computationList}


def deleteComputation(
        computationGUID: str,
        identifierCollection: pymongo.collection.Collection,
        userCollection: pymongo.collection.Collection 
    ) -> tuple[Computation, OperationStatus]:
    ''' Delete a computation and any triples from other relations
    '''

    # check that computation exists
    computationMetadata = identifierCollection.find_one(
            {"@id": computationGUID}, 
            projection={"_id": False}
            )

    if computationMetadata is None:
        return None, OperationStatus(False, "computation not found", 404)

    computationInstance = Computation.model_validate(computationMetadata)
    
    # update user
    updateUserResult = userCollection.update_one(
            {"@id": computationInstance.owner},
            {"$pull": {"computation": computationInstance.guid}}
            )

    # clear usedBy for software and dataset
    updateUsedByResult = identifierCollection.update_many(
            {"usedBy": {"$in": [computationInstance.guid] }},
            {"$pull": {"usedBy": computationInstance.guid}}
            )


    # update generated
    updateGeneratedResult = identifierCollection.update_many(
            {"@id": {"$in": [computationInstance.generated]}},
            {"$pull": {"generatedBy": computationInstance.guid}}
            )
    

    # 'delete the computation document'
    identifierCollection.update_one(
            {"@id": computationGUID, "@type": "evi:Computation"} ,
            {"active": False}
            )


    return computationInstance, OperationStatus(True, "", 201)


def updateComputation(
        computationGUID: str,
        computationUpdate: dict,
        identifierCollection: pymongo.collection.Collection
    ) -> OperationStatus:
    pass


def getComputation(
        computationGUID: str,
        identifierCollection: pymongo.collection.Collection
        )-> tuple[Computation, OperationStatus]:

    computationMetadata = identifierCollection.find_one(
            {
                "@id": computationGUID, 
                "@type": "evi:Computation"
            }, projection={"_id": False}
            )

    if computationMetadata is None:
        return None, OperationStatus(False, "computation not found", 404)

    computationInstance = Computation.model_validate(computationMetadata)
    return computationInstance, OperationStatus(True, "", 200)


class ResourceTuple(BaseModel):
    requests: str
    limits: str

class JobRequirements(BaseModel):
    storage: ResourceTuple
    cpu: ResourceTuple
    mem: ResourceTuple

class ComputationModel(FairscapeEVIBaseModel, extra = Extra.allow):
    metadataType: Literal['evi:Computation'] = Field(alias="@type")
    url: str
    owner: str
    author: str
    dateCreated: Optional[datetime] = Field(default=None)
    dateFinished: Optional[datetime] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    includedInDataCatalog: Optional[str] = Field(default=None)
    command: Optional[Union[str,List[str]]] = Field(default=None)
    usedSoftware: str
    usedDataset: List[str]
    generated: List[str]


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
            return OperationStatus(False, f"owner {self.owner.id} does not exist", 404)

        # check that software exists
        if type(self.usedSoftware) == str:
            software_id = self.usedSoftware
        else:
            software_id = self.usedSoftware.id
        if MongoCollection.find_one({"@id": software_id}) is None:
            return OperationStatus(False, f"software {software_id} does not exist", 404)

        for dataset in self.usedDataset:
            # check that datasets exist
            if type(dataset) == str:
                dataset_id = dataset
            else:
                dataset_id = dataset.id
            if MongoCollection.find_one({"@id": dataset_id}) is None:
                return OperationStatus(False, f"dataset {dataset_id} does not exist", 404)

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


    def run_custom_container(self, mongo_collection: pymongo.collection.Collection, minio_client) -> OperationStatus:
        """
        run_custom_container creates a local computation and evidence graph record for computations

        """
        # print(self.usedSoftware)
        # print(self.usedDataset)

        used_by_ids = []
        # for usedDataset in self.usedDataset:
        #    dataset = Dataset.construct(id=usedDataset)
        #    dataset.read(mongo_collection)
        #    used_by_ids.append(dataset.id)
        if type(self.usedSoftware) == str:
            software_id = self.usedSoftware
        else:
            software_id = self.usedSoftware.id

        found_software = Software.construct(id=software_id)
        read_software = found_software.read(mongo_collection)
        script_path = found_software.distribution[0].contentUrl
        used_by_ids.append(software_id)

        dataset_path = []
        for dataset in self.usedDataset:
            if type(dataset) == str:
                dataset_id = dataset
            else:
                dataset_id = dataset.id

            found_dataset = Dataset.construct(id=dataset_id)
            read_dataset = found_dataset.read(mongo_collection)
            dataset_path.append(found_dataset.distribution[0].contentUrl)
            used_by_ids.append(dataset_id)

        # add usedBy property to all datatsets and the software
        # used_by_ids = [dataset.id for dataset in self.usedDataset]

        update_many_result = mongo_collection.update_many(
            {"@id": {"$in": used_by_ids}},
            {"$push": {
                "evi:usedBy": {
                    "@id": self.id,
                    "@type": self.type,
                    "name": self.name
                }
            }})

        if update_many_result.modified_count != len(used_by_ids):
            return OperationStatus(False, "", 500)

        # script_path = self.usedSoftware.distribution[0].contentUrl
        # script_path = found_software.distribution[0].contentUrl

        # dataset_path = [dataset.distribution[0].contentUrl for dataset in self.usedDataset]
        # dataset_path = [dataset.distribution[0].contentUrl for dataset in self.usedDataset]

        # create a temporary landing folder for the output
        job_path = pathlib.Path(f"/tmp/{self.name}")
        input_directory = job_path / "input"
        software_directory = input_directory / "software"
        data_directory = input_directory / "data"
        output_directory = job_path / "output"

        software_directory.mkdir(parents=True)
        data_directory.mkdir(parents=True)
        output_directory.mkdir(parents=True)

        # download script
        script_filename = software_directory / pathlib.Path(script_path).name

        def get_minio_object(path, filename):
            try:
                get_software = minio_client.fget_object(
                    MINIO_BUCKET, path, filename
                )

                return None

            except Exception as e:
                return OperationStatus(False, f"minio downloading error {str(e)}", 500)

        # download script
        script_download_status = get_minio_object(script_path, str(script_filename))

        if script_download_status != None:
            return script_download_status

        # download all dataset files
        for dataset in dataset_path:
            dataset_filename = data_directory / pathlib.Path(dataset).name

            dataset_download_status = get_minio_object(dataset, str(dataset_filename))

            if dataset_download_status != None:
                return dataset_download_status

        # setup the container
        docker_client = docker.from_env()

        try:
            container = docker_client.containers.create(
                image=self.container,
                command=self.command,
                auto_remove=False,
                volumes={
                    str(job_path): {'bind': '/mnt/', 'mode': 'rw'},
                }
            )
        except Exception as e:
            return OperationStatus(False, f"error creating docker container {str(e)}", 500)

            # update metadata with container id
        self.containerId = container.id
        # self.dateCreated = datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S")

        update_metadata_results = mongo_collection.update_one({"@id": self.id}, {
            "$set": {"containerId": self.containerId, "dateCreated": self.dateCreated}})
        if update_metadata_results.modified_count != 1:
            return OperationStatus(False, "Failed to update mongo metadata", 500)

        try:
            container.start()
            return OperationStatus(True, "", 201)

        except Exception as e:
            return OperationStatus(False, f"error starting container: {str(e)}", 500)




def RegisterComputation(computation: Computation):
    """
    Given a computation ID first await the success or failure of the container in the ongoing computation.
    If successfull register all datasets in the output folder for the supplied computation, 
    and append the computation metadata with status of the containers execution and logs if applicable
    """

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

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

    job_path = pathlib.Path(f"/tmp/{computation.name}")
    output_directory = job_path / "output"

    # container exited gracefully
    if status == "exited" and exit_code == 0:
        generates = []
        # get all output files
        for output_file in Path(output_directory).rglob('*'):
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

                #create_status = data_download.create_metadata(mongo_collection)

                with open(output_file, "rb") as output_file_object:
                    upload_status = data_download.register(mongo_collection, minio_client, output_file_object)
                    if upload_status.success != True:
                        print('could not upload file file', output_file_object.name, upload_status.message)
                        return JSONResponse(
                            status_code=500,
                            content={"error": f"unable to upload object: {output_file}"}
                        )

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

    # clean up directories and files
    dir_to_clean = pathlib.Path(job_path)
    write_container_log(f"message: cleaning compute job directory: {dir_to_clean}")
    if dir_to_clean.exists() and dir_to_clean.is_dir():
       shutil.rmtree(dir_to_clean)
       write_container_log(f"message: compute job directory: {dir_to_clean} removed successfully")
    else:
       write_container_log(f"message: error removing compute job directory: {dir_to_clean}")
    print('Run Custom Container: All done')
