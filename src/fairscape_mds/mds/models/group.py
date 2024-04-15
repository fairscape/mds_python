from typing import Optional, List
from pydantic import Extra
from fairscape_mds.mds.models.fairscape_base import *
from fairscape_mds.mds.models.user import User
from fairscape_mds.mds.utilities.operation_status import OperationStatus
import pymongo
from bson.son import SON


class Group(FairscapeEVIBaseModel, extra=Extra.allow):
    context: dict = Field(
        default={
            "@vocab": "https://schema.org/", 
            "evi": "https://w3id.org/EVI#"
        },
        alias="@context"
    )
    metadataType: str = Field(default="Organization", alias="@type")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    members: List[constr(pattern=IdentifierPattern)] = Field(default=[])

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Add a new group and persist in mongo.

        This method preforms checks of the state of the database, making sure the owner and the group exists.
        If a member isn't found it is removed from the object, but the create operation still can succeed.

        This is check is preformed to avoid having to deal with partial rollbacks, and messy logic based on pymongo exceptions.
        If the bulk write operation should proceed. The group is inserted, the owner is updated, and so are all members.

        TODO can preform all of these mongo operations within two transactions
        One to check the status of the database

        Args:
            MongoCollection (pymongo.collection.Collection): _description_

        Returns:
            OperationStatus: Class containing the status of the operation along with any potential error message
        """

        # check that group doesn't already exist
        if MongoCollection.find_one({"@id": self.id}) is not None:
            return OperationStatus(False, "group already exists", 400)

        # check that owner exists
        if MongoCollection.find_one({"@id": self.owner.id}) is None:
            return OperationStatus(False, "owner does not exist", 404)

        # check that each member exists
        existing_members = [member for member in self.members if
                            MongoCollection.find_one({"@id": member.id}) is not None]
        self.members = existing_members

        # embeded bson documents to enable Mongo queries
        group_dict = self.dict(by_alias=True)

        # embeded bson document for owner
        group_dict["owner"] = SON([(key, value) for key, value in group_dict["owner"].items()])

        # embeded bson documents for all members
        group_dict["members"] = [SON([(key, value) for key, value in member.dict(by_alias=True).items()]) for member in
                                 self.members]

        # update operation for all the member users
        add_organization_update = {
            "$push": {"organizations": SON([("@id", self.id), ("@type", "Organization"), ("name", self.name)])}}

        group_bulk_write = [
            pymongo.InsertOne(group_dict),
            # update owner model to have listed the group
            pymongo.UpdateOne({"@id": self.owner.id}, add_organization_update)
        ]

        # for all users who are members of this group
        # modify their user record to remove this group
        for member in self.members:
            group_bulk_write.append(pymongo.UpdateOne({"@id": member.id}, add_organization_update))

        # preform the bulk write
        try:
            bulk_write_result = MongoCollection.bulk_write(group_bulk_write)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"create Organization error: {bwe}", 500)

        # check that one document was created
        if bulk_write_result.inserted_count != 1:
            return OperationStatus(False, f"create Organization error: {bulk_write_result.bulk_api_result}", 500)

        # TODO check that the transaction exists
        # bulk_write_result. = len(self.members) + 1

        return OperationStatus(True, "", 201)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """Delete the organization. Update all members and owner to remove the organization from their properties.

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
                return OperationStatus(False, "group not found", 404)
            else:
                return read_status

        # create a bulk write operation
        # to remove a document from a list
        pull_operation = {"$pull": {"organizations": {"@id": self.id}}}

        # for ever member, remove the Organization from their list of organizations
        bulk_edit = [pymongo.UpdateOne({"@id": member.id}, pull_operation) for member in self.members]

        # operations to modify the owner
        bulk_edit.append(
            pymongo.UpdateOne({"@id": self.owner.id}, pull_operation)
        )

        # operations to delete the organization document
        bulk_edit.append(
            pymongo.DeleteOne({"@id": self.id})
        )

        # run the transaction
        try:
            bulk_edit_result = MongoCollection.bulk_write(bulk_edit)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"Delete Organization Error: {bwe}", 500)

        # check that the document was deleted
        if bulk_edit_result.deleted_count == 1:
            return OperationStatus(True, "", 200)
        else:
            return OperationStatus(False, f"{bulk_edit_result.bulk_api_result}", 500)


    def add_user(self, MongoCollection: pymongo.collection.Collection, member_id) -> OperationStatus:
        # find the user
        group_user = User.construct(id=member_id)
        user_read_status = group_user.read(MongoCollection)

        if not user_read_status.success:
            return user_read_status


        # update the group to add the new user
        append_status = self.update_append(
            MongoCollection,
            "members",
            {
                "@id": group_user.id,
                "@type": "Person",
                "name": group_user.name,
                "email": group_user.email
            }
        )

        # update the user to show new membeship

        return OperationStatus(True, "", 200)



    def remove_user(self, MongoCollection: pymongo.collection.Collection, member_id) -> OperationStatus:
        # find the user
        group_user = User.construct(id=member_id)

        user_read_status = group_user.read(MongoCollection)

        if not user_read_status.success:
            return user_read_status

        # update the group to remove the user
        append_status = self.update_remove(
            MongoCollection,
            "members",
            group_user.id,
        )

        # update the user to reflect the changed membership


        return OperationStatus(True, "", 200)


def list_groups(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "Organization"},
        projection={"_id": False}
    )
    return {"groups":  [{"@id": group.get("@id"), "@type": "Organization", "name": group.get("name")} for group in cursor] }
















