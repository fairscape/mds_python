from bson import SON
from pydantic import (
    Extra,
    Field,
)
from typing import Optional, List, Union, Literal
from datetime import datetime
from pymongo.collection import Collection

from fairscape_mds.models.fairscape_base import *
from fairscape_mds.utilities.operation_status import OperationStatus
 


class Dataset(FairscapeEVIBaseModel, extra=Extra.allow):
    owner: str = Field(...)
    metadataType: str = Field(
        title="metadataType",
        alias="@type",
        default="evi:Dataset"
    )
    distribution: Optional[List[str]] = Field(default=[])
    includedInDataCatalog: Optional[str] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    dateCreated: Optional[datetime] = Field(default_factory=datetime.now)
    dateModified: Optional[datetime] = Field(default_factory=datetime.now)
    usedBy: Optional[List[str]] = Field(default=[])
    generatedBy: Optional[str] = Field(default=None)


    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

        # TODO e.g. when dataset is updated, it should be reflected in its owners profile
        return super().update(MongoCollection)


class DatasetCreateModel(BaseModel, extra=Extra.allow):
    guid: str = Field(
        title="guid",
        alias="@id"
    )
    name: str
    description: str
    keywords: List[str]
    owner: str = Field(...)
    includedInDataCatalog: Optional[str] = Field(default=None)
    sourceOrganization: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    dateCreated: Optional[datetime] = Field(default_factory=datetime.now)
    dateModified: Optional[datetime] = Field(default_factory=datetime.now)
    usedBy: Optional[List[str]] = Field(default=[])
    generatedBy: Optional[str] = Field(default=None)


    def convert(self)-> Dataset:

        return Dataset(
                guid=self.guid,
                name=self.name,
                description=self.description,
                keywords=self.keywords,
                owner=self.owner,
                distribution=[],
                includedInDataCatalog=self.includedInDataCatalog,
                sourceOrganization=self.sourceOrganization,
                author=self.author,
                dateCreated=self.dateCreated,
                dateModified=self.dateModified,
                published=True
                )



def updateEVIUsedBy(
    datasetInstance: Dataset,
    identifierCollection: pymongo.collection.Collection
        ):
    if len(datasetInstance.usedBy) != 0:
        # for every used by 
        for computationGUID in list(filter(lambda x: 'ark:' in x, test_list)):
            # 
            computationMetadata = identifierCollection.find_one(
                    {
                        "@id": computationGUID, 
                        "@type": "evi:Computation"
                        } 
                    )
            
            if computationMetadata is None:
                return OperationStatus(
                        False, 
                        f"dataset property usedBy {computationGUID} computation not found", 
                        404
                        )
        
            # is this dataset listed as an output of the existing computation
            if computationGUID not in computationMetadata.get("usedDataset"):
                updateComputationResult = identifierCollection.update_one({
                    "@id": computationGUID, 
                    "@type": "evi:Computation"
                    },
                    {"$push": {"usedDataset": computationGUID}}
                )
            
                # check updating result
                if updateComputationResult.modified_count != 1:
                    return OperationStatus(
                            False,
                            f"failed to update computation specified by dataset.usedBy {datasetInstance.usedBy}",
                            500
                            )

    return None


def updateEVIGeneratedBy(
    datasetInstance: Dataset,
    identifierCollection: pymongo.collection.Collection
    ):
    # must check that generatedBy is an ark
    if 'ark:' in datasetInstance.generatedBy:
        computationMetadata = identifierCollection.find_one(
                {
                    "@id": datasetInstance.generatedBy, 
                    "@type": "evi:Computation"
                    } 
                )
        
        if computationMetadata is None:
            return OperationStatus(
                    False, 
                    f"dataset property generatedBy {datasetInstance.generatedBy} computation not found", 
                    404
                    )

        # is this dataset listed as an output of the existing computation
        if datasetInstance.guid not in computationMetadata.get("generated"):
            updateComputationResult = identifierCollection.update_one({
                "@id": datasetInstance.generatedBy, 
                "@type": "evi:Computation"
                },
                {"$push": {"generated": datasetInstance.guid}}
            )

            # check updating result
            if updateComputationResult.modified_count != 1:
                return OperationStatus(
                        False,
                        f"failed to update computation specified by dataset.generatedBy {datasetInstance.generatedBy}",
                        500
                        )

    return None



def createDataset(
    datasetInstance: Dataset,
    identifierCollection: pymongo.collection.Collection,
    userCollection: pymongo.collection.Collection
    )-> OperationStatus:
    # check that dataset does not already exist
    if identifierCollection.find_one({"@id": datasetInstance.guid}) is not None:
        return OperationStatus(False, "dataset already exists", 400)
    
    # check that owner exists
    if userCollection.find_one({"@id": datasetInstance.owner}) is None:
        return OperationStatus(False, "owner does not exist", 404)

    # if generatedBy is an ark
    # make sure it exists in the database as a computation
    #if datasetInstance.generatedBy is not None:
    #    updateGeneratedByResult = updateEVIGeneratedBy(datasetInstance, identifierCollection)

    #    if updateGeneratedByResult:
    #        return updateGeneratedByResult
    
    #if datasetInstance.usedBy is not None:
    #    updateUsedByResult = updateEVIUsedBy(datasetInstance, identifierCollection)

    #    if updateUsedByResult:
    #        return updateUsedByResult


    # insert dataset
    datasetMetadata = datasetInstance.model_dump(by_alias=True)
    insertResult = identifierCollection.insert_one(
        datasetMetadata
        )

    # check the insert one results
    if insertResult.inserted_id is None:
        return OperationStatus(False, f"error inserting document: {str(datasetMetadata)}", 500)
        

    # update operations for the owner user of the dataset
    updateResult = userCollection.update_one(
        {"@id": datasetInstance.owner}, 
        {"$push": {"datasets": datasetInstance.guid}}
        )

    # check that the update operation succeeded
    if updateResult.modified_count != 1:
        identifierCollection.delete_one({"@id": datasetInstance.guid})
        return OperationStatus(False, f"error updating user on dataset create", 500)
    
    # TODO update organization

    # TODO update project 
 
    return OperationStatus(True, "", 201)


def deleteDataset(
    datasetGUID: str,
    identifierCollection: pymongo.collection.Collection, 
    userCollection: pymongo.collection.Collection
) -> tuple[Dataset, OperationStatus]:
    """Delete the dataset. Update each user who is an owner of the dataset.

    Args:
        MongoCollection (pymongo.collection.Collection): _description_

    Returns:
        OperationStatus: _description_
    """

    # check that record exists
    # also, if successfull, will unpack the data we need to build the update operation
    datasetMetadata = identifierCollection.find_one({
        "@id": datasetGUID,
        "@type": "evi:Dataset"
        },
        projection={"_id": False}
        ) 



    if datasetMetadata is None:
        return None, OperationStatus(False, "dataset not found", 404)


    datasetInstance = Dataset.model_validate(datasetMetadata)

    # if dataset has been deleted already
    if not datasetInstance.published:
        return datasetInstance, OperationStatus(False, "dataset has been deleted", 400)

    pullOperation = {"$pull": {"datasets": datasetGUID}}

    #  update the owner to remove the dataset
    updateOwner = userCollection.update_one(
        {"@id": datasetInstance.owner}, 
        pullOperation
    )

    if updateOwner.modified_count != 1:
        return datasetInstance, OperationStatus(False, "failed to update owner", 500)

    # update the project to remove the dataset
    if datasetInstance.includedInDataCatalog is not None:
        updateProject = identifierCollection.update_one(
            {"@id": datasetInstance.includedInDataCatalog}, 
            pull_operation, 
            )

    if datasetInstance.sourceOrganization is not None:
        update_organization = IdentifierCollection.update_one(
            {"@id": datasetInstance.sourceOrganization},
            pull_operation, 
            )

    # TODO delete all distributions 
    if len(datasetInstance.distribution) != 0:
        distributionGUIDS= datasetInstance.distribution
        #delete_status = delete_distribution_metadata(distribution_identifiers)
        

    # delete the distribution
    updateDataset = identifierCollection.update_one(
            {"@id": datasetGUID, "@type": "evi:Dataset"},
            {"$set":{"published": False, "distribution": []}}
            )
        
    if updateDataset.modified_count != 1:
        return datasetInstance, OperationStatus(False, "", 500)

    return datasetInstance, OperationStatus(True, "", 200)


def deleteDownload(
    identifier_collection: Collection,
    user_collection: Collection,
    minio_client,
    download_identifier,
) -> tuple[Dataset, OperationStatus]:
    '''
    '''
    pass



def listDatasets(mongo_collection: Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Dataset"},
        projection={"_id": False, }
    )
    dataset_list = [
            {
                "@id": dataset.get("@id"), 
                "@type": "evi:Dataset", 
                "name": dataset.get("name")
            } for dataset in cursor
        ]
    return {"datasets": dataset_list }
