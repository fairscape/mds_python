from bson import SON
from pydantic import (
    Extra,
    Field,
    constr
)
from typing import List, Union, Optional
from fairscape_mds.mds.models.fairscape_base import *


class Project(FairscapeBaseModel, extra = Extra.allow):
    metadataType: str = Field(default="Project", alias="@type")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    members: List[constr(pattern=IdentifierPattern)] = []
    memberOf: constr(pattern=IdentifierPattern) = Field(...)
    datasets: Optional[List[constr(pattern=IdentifierPattern)]]
    computations: Optional[List[constr(pattern=IdentifierPattern)]]
    software: Optional[List[constr(pattern=IdentifierPattern)]]
    evidencegraphs: Optional[List[constr(pattern=IdentifierPattern)]]
    rocrates: Optional[List[constr(pattern=IdentifierPattern)]]


    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO initialize attributes of project
        # datasets: List[DatasetCompactView]
        # computations: List[ComputationCompactView]
        # software: List[SoftwareCompactView]
        # evidencegraphs: List[EvidenceGraphCompactView]
        # acl

        # check that project does not already exist
        if MongoCollection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "project already exists", 400)

        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner.id}) is None:
            return OperationStatus(False, "owner does not exist", 404)


        if MongoCollection.find_one({"@id": self.memberOf.id}) is None:
            return OperationStatus(False, "Organization does not exist", 404)

        # embeded bson documents to enable Mongo queries
        project_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        project_dict["owner"] = SON([(key, value) for key, value in project_dict["owner"].items()])

        # update operations for the owner user of the project
        add_project_update = {
            "$push": {"projects": SON([("@id", self.id), ("@type", "Project"), ("name", self.name)])}
        }

        project_bulk_write = [
            pymongo.InsertOne(project_dict),
            # update owner model to have listed the project
            pymongo.UpdateOne({"@id": self.owner.id}, add_project_update),
            pymongo.UpdateOne({"@id": self.memberOf.id}, add_project_update)
        ]

        # perform the bulk write
        try:
            bulk_write_result = MongoCollection.bulk_write(project_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"error performing bulk write operations: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create project error: {bulk_write_result.bulk_api_result}", 500)

        return OperationStatus(True, "", 201)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO e.g. when project is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Delete the project. Update each user who is an owner of the project.

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
                return OperationStatus(False, "project not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"projects": {"@id": self.id}}}

        # for ever member, remove the project from their list of project
        # bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit = [
            pymongo.UpdateOne({"@id": self.owner.id}, pull_operation)
        ]

        # operations to delete the project document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.id})
        )

        # run the transaction
        try:
            bulk_edit_result = MongoCollection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete Project Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)


def list_project(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "Project"},
        projection={"_id": False}
    )
    return {"projects": [{"@id": project.get("@id"), "@type": "Project", "name": project.get("name")} for project in
                         cursor]}
