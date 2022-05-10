from typing import Optional

from pydantic import Extra

from mds.models.compact.organization import OrganizationCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.fairscape_base import *
from mds.utilities.operation_status import OperationStatus
from mds.utilities.utils import validate_email


class User(FairscapeBaseModel, extra=Extra.allow):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "Person"
    email: str
    password: str
    organizations: Optional[List[OrganizationCompactView]] = []
    # projects: Optional[List[ProjectCompactView]] = []
    # datasets: Optional[List[DatasetCompactView]] = []
    software: Optional[List[SoftwareCompactView]] = []
    # computations: Optional[List[ComputationCompactView]] = []

    validate_email = validator('email', allow_reuse=True)(validate_email)

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # creating a new user we must set their owned objects to none
        # self.projects = []
        # self.datasets = []
        self.software = []
        # self.computations = []

        return super().create(MongoCollection, None)  # Does not work without bson positional parameter

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO Make sure user doesn't have any owned resources
        return super().delete(MongoCollection)


def list_users(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "Person"},
        projection={"_id": False}
    )
    return [{"@id": user.get("@id"), "name": user.get("name")} for user in cursor]