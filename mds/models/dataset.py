from bson import SON
from pydantic import (
    Extra,
    Field,
)
from typing import Optional, List, Union
from datetime import datetime
from pymongo.collection import Collection

from mds.models.fairscape_base import *
from mds.models.utils import (
    delete_distribution_metadata
)
from mds.utilities.operation_status import OperationStatus
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

class Dataset(FairscapeBaseModel, extra=Extra.allow):
    metadataType: str = Field(default="evi:Dataset", alias="@type")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    distribution: Optional[List[str]] = []
    includedInDataCatalog: Optional[str] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    dateCreated: Optional[datetime] = Field(default_factory=datetime.now)
    dateModified: Optional[datetime] = Field(default_factory=datetime.now)
    usedBy: Optional[List[str]] = []


    def create(
        self, 
        IdentifierCollection: pymongo.collection.Collection, 
        UserCollection: pymongo.collection.Collection
    ) -> OperationStatus:

        # TODO initialize attributes of dataset
        self.distribution = []
        # self.dateCreated = ""
        # self.dateModified = ""
        # self.activity = []

        # check that dataset does not already exist
        if IdentifierCollection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "dataset already exists", 400)



        # check that owner exists
        if UserCollection.find_one({"@id": self.owner.id}) is None:
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


        # use a session and transaction to enable rollbacks on errors 
        insert_result = IdentifierCollection.insert_one(
            dataset_dict)


        # check the insert one results
        if insert_result.inserted_id is None:
            return OperationStatus(False, f"error inserting document: {str(dataset_dict)}", 500)

        # update owner model to have listed the dataset
        update_result = UserCollection.update_one(
            {"@id": self.owner.id}, 
            add_dataset_update,
            )

        # check that the update operation succeeded
        if update_result.modified_count != 1:
            IdentifierCollection.delete_one({"@id": self.id})
            return OperationStatus(False, f"error updating user on dataset create", 500)
 
        return OperationStatus(True, "", 201)


    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO e.g. when dataset is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)


    def delete(
        self, 
        IdentifierCollection: pymongo.collection.Collection, 
        UserCollection: pymongo.collection.Collection
    ) -> OperationStatus:
        """Delete the dataset. Update each user who is an owner of the dataset.

        Args:
            MongoCollection (pymongo.collection.Collection): _description_

        Returns:
            OperationStatus: _description_
        """

        # check that record exists
        # also, if successfull, will unpack the data we need to build the update operation
        read_status = self.read(IdentifierCollection)

        if not read_status.success:
            if read_status.status_code == 404:
                return OperationStatus(False, "dataset not found", 404)
            else:
                return read_status


        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"datasets": {"@id": self.id}}}

        #  update the owner to remove the dataset
        update_owner = UserCollection.update_one(
            {"@id": self.owner.id}, 
            pull_operation, 
        )

        if update_owner.modified_count != 1:
            return OperationStatus(False, "", 500)

        # update the project to remove the dataset
        if self.includedInDataCatalog is not None:
            update_project = IdentifierCollection.update_one(
                {"@id": self.includedInDataCatalog}, 
                pull_operation, 
                )

            if update_project.modified_count == 0:
                return OperationStatus(False, "", 500)

            # update the organization to remove the dataset
        if self.sourceOrganization is not None:
            update_organization = IdentifierCollection.update_one(
                {"@id": self.sourceOrganization},
                pull_operation, 
                )

        if update_organization.modified_count != 1:
            return OperationStatus(False, "", 500)

        # TODO delete all distributions 
        if len(self.distribution) != 0:
            distribution_identifiers = [ dist['@id'] for dist in self.distribution ]
            delete_status = delete_distribution_metadata(distribution_identifiers)
            

        # delete the distribution
        delete_dataset = pymongo.delete_one({"@id": self.id})
            
        if delete_dataset.deleted_count != 1:
            return OperationStatus(False, "", 500)

        return OperationStatus(True, "", 200)

def DeleteDataset(
    identifier_collection: Collection, 
    user_collection: Collection,
    dataset_id: str
):
    """
    """
    pass


def DeleteDownload(
    identifier_collection: Collection,
    user_collection: Collection,
    minio_client,
    download_identifier,
):
    """
    """
    pass
