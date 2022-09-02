from bson import SON
from pydantic import Extra
from typing import Optional, List, Union
from datetime import datetime
import pymongo

from mds.models.fairscape_base import *
from mds.models.compact import *
from mds.utilities.operation_status import OperationStatus
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

class Dataset(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "evi:Dataset"
    owner: UserCompactView
    distribution: Optional[List[DataDownloadCompactView]] = []
    includedInDataCatalog: Optional[ProjectCompactView] = None
    sourceOrganization: Optional[OrganizationCompactView] = None
    author: Optional[Union[str, UserCompactView]] = ""
    dateCreated: Optional[datetime]
    dateModified: Optional[datetime]
    activity: Optional[List[ComputationCompactView]] = []
    acl: Optional[dict]

    class Config:
        extra = Extra.allow

    def create(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        # TODO initialize attributes of dataset
        self.distribution = []
        # self.dateCreated = ""
        # self.dateModified = ""
        # self.activity = []

        MongoDatabase = MongoClient[MONGO_DATABASE]
        MongoCollection = MongoDatabase[MONGO_COLLECTION]

        # start a single session
        session = MongoClient.start_session()

        # check that dataset does not already exist
        if MongoCollection.find_one({"@id": self.id}, session=session) is not None:
            session.end_session()
            return OperationStatus(False, "dataset already exists", 400)



        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner.id}, session=session) is None:
            session.end_session()
            return OperationStatus(False, "owner does not exist", 404)

        # embeded bson documents to enable Mongo queries
        dataset_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        dataset_dict["owner"] = SON([
            (key, value) for key, value in dataset_dict["owner"].items()
            ])


        # update operations for the owner user of the dataset
        add_dataset_update = {
            "$push": {"datasets": SON([("@id", self.id), ("@type", "evi:Dataset"), ("name", self.name)])}
        }

        undo = []

        # use a session and transaction to enable rollbacks on errors 
        insert_result = MongoCollection.insert_one(
            dataset_dict, session=session)


        # check the insert one results
        if insert_result.inserted_id is None:
            return OperationStatus(False, f"error inserting document: {str(dataset_dict)}", 500)

        # update owner model to have listed the dataset
        update_result = MongoCollection.update_one(
            {"@id": self.owner.id}, 
            add_dataset_update, 
            session=session
            )

        # check that the update operation succeeded
        if update_result.modified_count != 1:
            MongoCollection.delete_one({"@id": self.id})
            return OperationStatus(False, f"error updating user on dataset create", 500)
 
        return OperationStatus(True, "", 201)


    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO e.g. when dataset is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)


    def delete(self, MongoClient: pymongo.MongoClient) -> OperationStatus:
        """Delete the dataset. Update each user who is an owner of the dataset.

        Args:
            MongoCollection (pymongo.collection.Collection): _description_

        Returns:
            OperationStatus: _description_
        """

        MongoDatabase = MongoClient[MONGO_DATABASE]
        MongoCollection = MongoDatabase[MONGO_COLLECTION]
        session = MongoClient.start_session()

        # check that record exists
        # also, if successfull, will unpack the data we need to build the update operation
        read_status = self.read(MongoCollection)

        if not read_status.success:
            if read_status.status_code == 404:
                return OperationStatus(False, "dataset not found", 404)
            else:
                return read_status


        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"datasets": {"@id": self.id}}}

        with session.start_transaction() as transaction:


            #  update the owner to remove the dataset
            update_owner = MongoCollection.update_one(
                {"@id": self.owner.id}, pull_operation, session=session)

            if update_owner.modified_count != 1:
                # cancel transaction
                session.abort_transaction()
                return OperationStatus(False, "", 500)

            # update the project to remove the dataset
            if self.includedInDataCatalog is not None:
                update_project = MongoCollection.update_one(
                    {"@id": self.includedInDataCatalog}, 
                    pull_operation, 
                    session=session
                    )

                if update_project.modified_count != 1:
                    # cancel transaction
                    session.abort_transaction()
                    return OperationStatus(False, "", 500)

            # update the organization to remove the dataset
            if self.sourceOrganization is not None:
                update_organization = MongoCollection.update_one(
                    {"@id": self.sourceOrganization},
                    pull_operation, 
                    session=session
                    )

                if update_organization.modified_count != 1:
                    # cancel transaction
                    session.abort_transaction()
                    return OperationStatus(False, "", 500)

            # TODO delete all distributions 
            if len(self.distribution) != 0:
                pass
            

            # delete the distribution
            delete_dataset = pymongo.delete_one({"@id": self.id})
            
            if delete_dataset.deleted_count != 1:

                # cancel transaction
                session.abort_transaction()
                return OperationStatus(False, "", 500)

            session.commit_transaction()


        return OperationStatus(True, "", 200)


def list_dataset(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Dataset"},
        projection={"_id": False}
    )
    return {"datasets": [{"@id": dataset.get("@id"), "@type": "evi:Dataset", "name": dataset.get("name")} for dataset in
                         cursor]}
