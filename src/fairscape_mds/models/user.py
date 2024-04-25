from typing import Optional

import crypt
from pydantic import Extra

from fairscape_mds.models.fairscape_base import *
from fairscape_mds.utilities.operation_status import OperationStatus
from fairscape_mds.utilities.utils import validate_email

class User(FairscapeBaseModel, extra=Extra.allow):
    context: dict = Field( 
        default= {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context" 
    )
    metadataType: str = Field(alias="@type", default= "Person")
    email: str
    password: str
    organizations: Optional[List[str]] = Field(default=[])
    projects: Optional[List[str]] = Field(default= [])
    datasets: Optional[List[str]] = Field(default= [])
    downloads: Optional[List[str]] = Field(default= [])
    rocrates: Optional[List[str]] = Field(default= [])
    software: Optional[List[str]] = Field(default= [])
    computations: Optional[List[str]] = Field(default= [])
    evidencegraphs: Optional[List[str]] = Field(default= [])

    validate_email = validator('email', allow_reuse=True)(validate_email)


class UserReadModel(BaseModel):
    context: dict = Field( 
        default= {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context" 
    )
    metadataType: str = Field(alias="@type", default= "Person")
    email: str
    organizations: Optional[List[str]] = Field(default=[])
    projects: Optional[List[str]] = Field(default= [])
    datasets: Optional[List[str]] = Field(default= [])
    downloads: Optional[List[str]] = Field(default= [])
    rocrates: Optional[List[str]] = Field(default= [])
    software: Optional[List[str]] = Field(default= [])
    computations: Optional[List[str]] = Field(default= [])
    evidencegraphs: Optional[List[str]] = Field(default= [])



def updateUser():
    pass


def createUser(
    userInstance: User, 
    passwordSalt: str,
    userCollection: pymongo.collection.Collection
    ):

    # check that user doesn't already exist
    foundUserMetadata = userCollection.find_one({"@id": userInstance.guid})

    if foundUserMetadata is not None:
        return OperationStatus(False, "user already exists", 400)

    # hash password 
    userInstance.password = crypt.crypt(userInstance.password, passwordSalt)

    userMetadata = userInstance.model_dump(by_alias=True)
    userCollection.insert_one(userMetadata)

    return OperationStatus(True, "", 201)


def getUserByGUID(
    userGUID: str, 
    userCollection: pymongo.collection.Collection
    ):

    foundUserMetadata = userCollection.find_one({"@id": userGUID}, projection={"_id": False, "password": False})
    if foundUserMetadata is None:
        return None, OperationStatus(False, "user not found", 404)

    else:
        return UserReadModel.model_validate(foundUserMetadata), OperationStatus(True, "", 200)

    

def getUserByEmail(email, userCollection):
    foundUser = userCollection.find_one({"email": email}, projection={"_id": False})

    if foundUser is None:
        return None, OperationStatus(False, "user not found", 404)

    else:
        foundUserModel = User.model_validate(foundUser)
        return foundUserModel, OperationStatus(True, "", 200)


def deleteUserByGUID(
    user_id: str,
    mongo_collection: pymongo.collection.Collection, 
    )-> dict:
    ''' Delete a user by setting their account status to deactivated

    - TODO Preserves all their metadata.
    - TODO removes their ability to login
    - TODO in order to delete account all files must be given admin access to 
        another individual
    '''
    
    deleted_user = mongo_collection.find_one_and_delete({"@id": user_id})
    return deleted_user


def listUsers(identifierCollection: pymongo.collection.Collection):
    cursor = identifierCollection.find(
        filter={"@type": "Person"},
        projection={"_id": False}
    )
    return {"users":  [{"@id": user.get("@id"), "@type": "Person", "name": user.get("name")} for user in cursor] }

