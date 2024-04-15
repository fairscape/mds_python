from typing import Optional

from pydantic import Extra

from fairscape_mds.models.fairscape_base import *
from fairscape_mds.utilities.operation_status import OperationStatus
from fairscape_mds.utilities.utils import validate_email


def getUserByID():
    pass

def updateUser():
    pass

def listUsers(mongo_collection: pymongo.collection.Collection):
   
    user_cursor = mongo_collection.find(
        query={"@type": "Person"}, 
        projection={"@id": True, "name": True, "email": True}
        )
    

    pass


def deleteUserByGUID(
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
    context: dict = Field( 
        default= {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context" 
    )
    metadataType: str = Field(alias="@type", default= "Person")
    email: str
    password: str
    organizations: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    datasets: Optional[List[str]] = []
    downloads: Optional[List[str]] = []
    rocrates: Optional[List[str]] = []
    software: Optional[List[str]] = []
    computations: Optional[List[str]] = []
    evidencegraphs: Optional[List[str]] = []

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


def listUsers(identifierCollection: pymongo.collection.Collection):
    cursor = identifierCollection.find(
        filter={"@type": "Person"},
        projection={"_id": False}
    )
    return {"users":  [{"@id": user.get("@id"), "@type": "Person", "name": user.get("name")} for user in cursor] }

