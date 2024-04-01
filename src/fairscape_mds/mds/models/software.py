from bson import SON
from pydantic import (
    Extra,
    Field,
    constr
)
from typing import Optional, List
from fairscape_mds.mds.models.fairscape_base import *


class Software(FairscapeBaseModel, extra = Extra.allow):
    metadataType: str = Field(default="evi:Software")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    # author: str
    # citation: str
    distribution: List[constr(pattern=IdentifierPattern)] = Field(default=[])
    usedBy: List[constr(pattern=IdentifierPattern)] = Field(default=[])
    sourceOrganization: constr(pattern=IdentifierPattern) = Field(default=None)
    includedInDataCatalog: constr(pattern=IdentifierPattern) = Field(default=None)



    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # initialize empty list of computation for a software
        # self.usedBy = []

        # check that software does not already exist
        if MongoCollection.find_one({"@id": self.guid}) is not None:
            return OperationStatus(False, "software already exists", 400)

        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner}) is None:
            return OperationStatus(False, "owner does not exist", 404)

        # embeded bson documents to enable Mongo queries
        software_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        #software_dict["owner"] = SON([(key, value) for key, value in software_dict["owner"].items()])

        # update operations for the owner user of the software
        add_software_update = {
            "$push": {"software": SON([("@id", self.guid), ("@type", "evi:Software"), ("name", self.name)])}
        }

        software_bulk_write = [
            pymongo.InsertOne(software_dict),
            # update owner model to have listed the software
            pymongo.UpdateOne({"@id": self.owner}, add_software_update)
        ]

        # perform the bulk write
        try:
            bulk_write_result = MongoCollection.bulk_write(software_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"error performing bulk write operations: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create software error: {bulk_write_result.bulk_api_result}", 500)

        return OperationStatus(True, "", 201)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO e.g. when software name is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Delete the software. Update each user who is an owner of the software.

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
                return OperationStatus(False, "software not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"software": {"@id": self.guid}}}

        # for ever member, remove the software from their list of software
        # bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit = [
            pymongo.UpdateOne({"@id": self.owner}, pull_operation)
        ]

        # operations to delete the software document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.guid})
        )

        # run the transaction
        try:
            bulk_edit_result = MongoCollection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete Software Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)


def list_software(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Software"},
        projection={"_id": False}
    )
    return {
        "software": [{"@id": software.get("@id"), "@type": "evi:Software", "name": software.get("name")} for software in
                     cursor]}
