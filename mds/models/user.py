from typing import List, Literal, Tuple
from pydantic import EmailStr, Extra
from .utils import FairscapeBaseModel, OrganizationCompactView, ProjectCompactView, DatasetCompactView, SoftwareCompactView, ComputationCompactView, OperationStatus
import pymongo


class User(FairscapeBaseModel, extra=Extra.allow):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type = "Person"
    email: EmailStr  # requires installation of module email-validator
    password: str
    is_admin: bool
    organizations: list[OrganizationCompactView]
    projects: List[ProjectCompactView]
    datasets: List[DatasetCompactView]
    software: List[SoftwareCompactView]
    computations: List[ComputationCompactView]


    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus: 

        # creating a new user we must set their owned objects to none
        self.projects = []
        self.datasets = []
        self.software = []
        self.computations = []

        return super().create(MongoCollection)


    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)


    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().delete(MongoCollection)


    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus: 
        return super().update()
 
    
    def addOrganization(self, MongoCollection: pymongo.collection.Collection, Organization: OrganizationCompactView):
        return self.update_append(MongoCollection, "organizations", Organization)


    def removeOrganization(self, MongoCollection: pymongo.collection.Collection, Organization: OrganizationCompactView):
        return self.update_remove(MongoCollection, "organizations", Organization)


    def addProject(self, MongoCollection: pymongo.collection.Collection, Project: ProjectCompactView):
        return self.update_append(MongoCollection, "projects", Project)


    def removeProject(self, MongoCollection: pymongo.collection.Collection, Project: ProjectCompactView):
        return self.update_remove(MongoCollection, "projects", Project)


    def addDataset(self, MongoCollection: pymongo.collection.Collection, Dataset: DatasetCompactView):
        return self.update_append(MongoCollection, "datasets", Dataset)


    def removeDataset(self, MongoCollection: pymongo.collection.Collection, Dataset: DatasetCompactView):
        return self.update_remove(MongoCollection, "datasets", Dataset)


    def addSoftware(self, MongoCollection: pymongo.collection.Collection, Software: SoftwareCompactView):
        return self.update_append(MongoCollection, "software", Software)


    def removeSoftware(self, MongoCollection: pymongo.collection.Collection, Software: SoftwareCompactView):
        return self.update_remove(MongoCollection, "software", Software)


    def addComputation(self, MongoCollection: pymongo.collection.Collection, Computation: ComputationCompactView):
        return self.update_append(MongoCollection, "computations", Computation)


    def removeComputation(self, MongoCollection: pymongo.collection.Collection, Computation: ComputationCompactView):
        return self.update_remove(MongoCollection, "computations", Computation)




