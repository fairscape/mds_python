from typing import Optional

from pydantic import Extra

from mds.models.compact.organization import OrganizationCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView
from mds.models.compact.rocrate import ROCrateCompactView
from mds.models.compact.computation import ComputationCompactView
from mds.models.compact.project import ProjectCompactView
from mds.models.compact.evidencegraph import EvidenceGraphCompactView
from mds.models.fairscape_base import *
from mds.utilities.operation_status import OperationStatus
from mds.utilities.utils import validate_email


def getUserByID():
    pass

def updateUser():
    pass

def listUsers(mongo_collection: pymongo.collection.Collection):
    
    pass


def deleteUserByID(
    mongo_collection: pymongo.collection.Collection, 
    user_id: str
    )-> dict:
    ''' Delete a user by setting their account status to deactivated

    - TODO Preserves all their metadata.
    - TODO removes their ability to login
    - TODO in order to delete account all files must be given admin access to 
        another individual
    '''
    
    deleted_user = mongo_collection.find_one_and_delete({"@id": user_id})
    return deleted_user


class User(FairscapeBaseModel, extra=Extra.allow):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "Person"
    email: str
    password: str
    organizations: Optional[List[OrganizationCompactView]] = []
    projects: Optional[List[ProjectCompactView]] = []
    datasets: Optional[List[DatasetCompactView]] = []
    rocrates: Optional[List[ROCrateCompactView]] = []
    software: Optional[List[SoftwareCompactView]] = []
    computations: Optional[List[ComputationCompactView]] = []
    evidencegraphs: Optional[List[EvidenceGraphCompactView]] = []

    validate_email = validator('email', allow_reuse=True)(validate_email)

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # creating a new user we must set their owned objects to none
        self.projects = []
        self.datasets = []
        self.rocrates = []
        self.software = []
        self.computations = []
        self.evidencegraphs = []

        return super().create(MongoCollection)

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
    return {"users":  [{"@id": user.get("@id"), "@type": "Person", "name": user.get("name")} for user in cursor] }

