from pydantic import (
    BaseModel, 
    validator,
    ConfigDict,
    Field,
    constr,
    Extra,
)

from typing import (
    List,
    Optional,
    Dict,
    Union
)


identifierPattern = "^ark[0-9]{5}:\/.*$"
defaultLicense = " https://creativecommons.org/licenses/by/4.0/"
defaultContext = {
    "@vocab": "https://schema.org/",
    "evi": "https://w3id.org/EVI#"
}


class Identifier(BaseModel, extra='allow'):
    guid: str = Field(
        title="guid",
        alias="@id"
    )
    metadataType: str = Field(
        title="metadataType",
        alias="@type"
    )
    name: str


class FairscapeBaseModel(Identifier):
    """Refers to the Fairscape BaseModel inherited from Pydantic

    Args:
        BaseModel (Default Pydantic): Every instance of the Fairscape BaseModel must contain
        an id, a type, and a name
    """
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra='allow'
    )
    context: Optional[Dict[str, str]] = Field(
        default=defaultContext,
        title="context",
        alias="@context"
    )
    url: Optional[str] = Field(default=None)


class FairscapeEVIBaseModel(FairscapeBaseModel):
    description: str = Field(min_length=5)
    workLicense: Optional[str] = Field(default=defaultLicense, alias="license")
    keywords: List[str] = Field(default=[])

class UserCreateModel(BaseModel):
    name: str
    email: str
    password: str

    validate_email = validator('email', allow_reuse=True)(validate_email)


class UserUpdateModel(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]


class UserReadModel(FairscapeBaseModel, extra=Extra.allow):
    metadataType: str = Field(alias="@type", default= "Person")
    name: str
    email: str
    password: str
    organizations: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    datasets: Optional[List[str]] = []
    rocrates: Optional[List[str]] = []
    software: Optional[List[str]] = []
    computations: Optional[List[str]] = []
    evidencegraphs: Optional[List[str]] = []


def createUser(userModel: UserCreateModel, collection: pymongo.Collection):

    #generateGUID()

    pass


def getUserByID(userID: str, collection: pymongo.Collection) -> UserReadModel:
    pass


def updateUser(userID: str, update: UserUpdate, collection: pymongo.Collection) -> UserReadModel:
    updateDictionary = userUpdate.model_dump()
    
    updateResult = collection.find_one_and_update(
            {"@id": userID},
            {"$set": updateDictionary},
            return_document = pymongo.collection.ReturnDocument.AFTER
            )

    if updateResult is None:
        raise Exception('user not found')

    return updateResult.model_validate(updateResult)


def userAddObject(userID: str, objectID: str, propertyName: str, collection: pymongo.Collection):
    ''' Method for materializing EVI object ark to user instance in user collection
    '''

    updateResult = collection.update_one(
            {"@id": userID},
            {"$push": {propertyName: objectID}}
            )

    if updateResult.matched_count != 1:
        raise Exception('user not found')

    if updateResult.modified_count != 1:
        raise Exception('user not modified')

    return None


def deleteUserByID(userID: str, collection: pymongo.Collection) -> UserReadModel:

    userRecord = collection.find_one({"@id": userID})

    if userRecord is None:
        raise Exception('user not found')

    # TODO cascase delete all user owned objects

    collection.delete_one({"@id": userID})

    return UserReadModel.model_validate(userRecord)


class DatasetCreateModel(BaseModel):
    name: str
    owner: constr(pattern=IdentifierPattern) = Field(...)
    author: Optional[str] = Field(default=None)
    includedInDataCatalog: Optional[str] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    dateCreated: Optional[datetime] = Field(default_factory=datetime.now)
    dateModified: Optional[datetime] = Field(default_factory=datetime.now)

class Dataset(FairscapeEVIBaseModel, extra=Extra.allow):
    metadataType: Literal['evi:Dataset'] = Field(alias="@type")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    distribution: Optional[List[str]] = []
    includedInDataCatalog: Optional[str] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    dateCreated: Optional[datetime] = Field(default_factory=datetime.now)
    dateModified: Optional[datetime] = Field(default_factory=datetime.now)
    usedBy: Optional[List[str]] = []


def createDataset(datasetInstance:DatasetCreateModel, collection: pymongo.Collection) -> DatasetReadModel:
    pass


def getDatasetByID(datasetID: str, collection: pymongo.Collection) -> DatasetReadModel:
    datasetMetadata = collection.find_one({"@id": datasetID})

    if datasetMetadata is None:
        raise Exception('dataset not found')

    return DatasetReadModel.model_validate(datasetMetadata)
    


class Organization(FairscapeEVIBaseModel, extra = Extra.allow):
    context: dict = Field(
        default={
            "@vocab": "https://schema.org/", 
            "evi": "https://w3id.org/EVI#"
        },
        alias="@context"
    )
    metadataType: str = Field(default="Organization", alias="@type")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    members: Optional[List[constr(pattern=IdentifierPattern)]] = Field(default=[])
    projects: Optional[List[constr(pattern=IdentifierPattern)]] = Field(default=[])



class Software(FairscapeEVIBaseModel, extra = Extra.allow):
    metadataType: str = Field(default="evi:Software")
    owner: constr(pattern=IdentifierPattern) = Field(...)
    # author: str
    # citation: str
    distribution: List[constr(pattern=IdentifierPattern)] = Field(default=[])
    usedBy: List[constr(pattern=IdentifierPattern)] = Field(default=[])
    sourceOrganization: constr(pattern=IdentifierPattern) = Field(default=None)
    includedInDataCatalog: constr(pattern=IdentifierPattern) = Field(default=None)


class Computation(FairscapeEVIBaseModel, extra = Extra.allow):
    metadataType: Literal['evi:Computation'] = Field(alias="@type")
    owner: constr(pattern=IdentifierPattern) 
    author: str
    dateCreated: Optional[datetime]
    dateFinished: Optional[datetime]
    # TODO check 
    sourceOrganization: constr(pattern=IdentifierPattern)
    sourceProject: constr(pattern=IdentifierPattern)
    container: str
    command: Optional[Union[str,List[str]]]
    usedSoftware: str
    usedDataset: str 
    containerId: Optional[str]
    #requirements: Optional[JobRequirements]
    generated: List[str]

class ROCrate(FairscapeBaseModel):
    guid: str = Field(alias="@id")
    metadataType: Optional[str] = Field(default="https://schema.org/Dataset", alias="@type")
    additionalType: Optional[str] = Field(default=ROCRATE_TYPE)
    name: constr(max_length=100)
    sourceOrganization: Optional[str] = Field(default=None)
    metadataGraph: List[Union[
        ROCrateDataset,
        ROCrateSoftware,
        ROCrateComputation,
        ROCrateDatasetContainer
    ]] = Field(alias="@graph", discriminator='additionalType')
    contentURL: Optional[str] = Field(
        default=None, 
        description="Value for ROCrate S3 URI of zip location"
        )
    distribution: Optional[ROCrateDistribution] = Field(default=None)
