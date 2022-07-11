from bson import SON
from pydantic import Extra
from typing import List, Union
from mds.models.fairscape_base import *
from mds.models.compact.user import UserCompactView


# from mds.models.compact.project import ProjectCompactView

class EvidenceGraph(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "evi:EvidenceGraph"
    owner: UserCompactView

    # graph: str

    class Config:
        extra = Extra.allow

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO initialize attributes of evidencegraph
        # self.graph = str

        # check that evidencegraph does not already exist
        if MongoCollection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "evidencegraph already exists", 400)

        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner.id}) is None:
            return OperationStatus(False, "owner does not exist", 404)

        # embeded bson documents to enable Mongo queries
        evidencegraph_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        evidencegraph_dict["owner"] = SON([(key, value) for key, value in evidencegraph_dict["owner"].items()])

        # update operations for the owner user of the evidencegraph
        add_evidencegraph_update = {
            "$push": {"evidencegraphs": SON([("@id", self.id), ("@type", "evi:EvidenceGraph"), ("name", self.name)])}
        }

        evidencegraph_bulk_write = [
            pymongo.InsertOne(evidencegraph_dict),
            # update owner model to have listed the evidencegraph
            pymongo.UpdateOne({"@id": self.owner.id}, add_evidencegraph_update)
        ]

        # perform the bulk write
        try:
            bulk_write_result = MongoCollection.bulk_write(evidencegraph_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"error performing bulk write operations: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create evidencegraph error: {bulk_write_result.bulk_api_result}", 500)

        return OperationStatus(True, "", 201)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO e.g. when evidencegraph is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Delete the evidencegraph. Update each user who is an owner of the evidencegraph.

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
                return OperationStatus(False, "evidencegraph not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"evidencegraphs": {"@id": self.id}}}

        # for ever member, remove the evidencegraph from their list of evidencegraph
        # bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit = [
            pymongo.UpdateOne({"@id": self.owner.id}, pull_operation)
        ]

        # operations to delete the evidencegraph document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.id})
        )

        # run the transaction
        try:
            bulk_edit_result = MongoCollection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete EvidenceGraph Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)


def list_evidencegraph(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:EvidenceGraph"},
        projection={"_id": False}
    )
    return {"evidencegraphs": [
        {"@id": evidencegraph.get("@id"), "@type": "evi:EvidenceGraph", "name": evidencegraph.get("name")} for
        evidencegraph in cursor]}
