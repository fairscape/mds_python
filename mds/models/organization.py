from bson import SON
from pydantic import Extra
from typing import List, Union, Optional
from mds.models.fairscape_base import *
from mds.models.compact.user import UserCompactView
from mds.models.compact.project import ProjectCompactView
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION


# from mds.models.compact.project import ProjectCompactView

class Organization(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "Organization"
    owner: Optional[UserCompactView] = []
    members: Optional[List[UserCompactView]] = []
    projects: Optional[List[ProjectCompactView]] = []

    class Config:
        extra = Extra.allow

    def create(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

        # TODO initialize attributes of organization
        # projects: List[ProjectCompactView]

        # check that organization does not already exist
        if mongo_collection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "organization already exists", 400)

        # check that owner exists
        if mongo_collection.find_one({"@id": self.owner.id}) is None:
            return OperationStatus(False, "owner does not exist", 404)

        # embeded bson documents to enable Mongo queries
        organization_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        organization_dict["owner"] = SON([(key, value) for key, value in organization_dict["owner"].items()])

        # update operations for the owner user of the organization
        add_organization_update = {
            "$push": {"organizations": SON([("@id", self.id), ("@type", "Organization"), ("name", self.name)])}
        }

        organization_bulk_write = [
            pymongo.InsertOne(organization_dict),
            # update owner model to have listed the organization
            pymongo.UpdateOne({"@id": self.owner.id}, add_organization_update)
        ]

        # perform the bulk write
        try:
            bulk_write_result = mongo_collection.bulk_write(organization_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"error performing bulk write operations: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create organization error: {bulk_write_result.bulk_api_result}", 500)


        # casbin add policies for ownership to mongo 
        #enforcer.add_policy(calling_user.id, "read", organization.id)
        #enforcer.add_policy(calling_user.id, "update", organization.id)
        #enforcer.add_policy(calling_user.id, "delete", organization.id)
        #enforcer.add_policy(calling_user.id, "createProject", organization.id)
        #enforcer.add_policy(calling_user.id, "manage", organization.id)
        #enforcer.save_policy()


        return OperationStatus(True, "", 201)


    def read(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        #if enforcer.enforce(calling_user.id, "read", organization_id) != True:
        #    return JSONResponse(
        #        status_code=401,
        #        content={
        #            "@id": organization_id,
        #            "error": "access not granted for read organization"
        #            }
        #    )

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]
        return super().read(mongo_collection)


    def update(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

        #if enforcer.enforce(calling_user.id, "update", organization.id) != True:
        #    return JSONResponse(
        #        status_code=401,
        #        content={"error": "user not permitted to update organization"}
        #    )

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

        # TODO e.g. when organization is updated, it should be reflected in its owners profile
        return super().update(mongo_collection)


    def delete(self, MongoClient: pymongo.MongoClient) -> OperationStatus:
        """Delete the organization. Update each user who is an owner of the organization.

        Args:
            MongoCollection (pymongo.collection.Collection): _description_

        Returns:
            OperationStatus: _description_
        """

        # TODO enforce permissions on delete
        #if enforcer.enforce(calling_user.id, "delete", organization_id) != True:
        #return JSONResponse(
        #    status_code=401,
        #    content={"error": "user not permitted to delete organization"}
        #)

        mongo_db = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_db[MONGO_COLLECTION]

        # check that record exists
        # also, if successfull, will unpack the data we need to build the update operation
        read_status = self.read(mongo_collection)

        if not read_status.success:
            if read_status.status_code == 404:
                return OperationStatus(False, "organization not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"organizations": {"@id": self.id}}}

        # for ever member, remove the organization from their list of organization
        # bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit = [
            pymongo.UpdateOne({"@id": self.owner.id}, pull_operation)
        ]

        # operations to delete the organization document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.id})
        )

        # run the transaction
        try:
            bulk_edit_result = mongo_collection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete Organization Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)


def list_organization(MongoClient: pymongo.Client):

    mongo_db = MongoClient[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    
    cursor = mongo_collection.find(
        filter={"@type": "Organization"},
        projection={"_id": False}
    )
    return {
        "organizations": [{"@id": organization.get("@id"), "@type": "Organization", "name": organization.get("name")}
                          for organization in cursor]}
