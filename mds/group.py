from pydantic import Extra
from typing import List, Literal
from mds.utils import FairscapeBaseModel, UserCompactView, OperationStatus
from pymongo.collection import Collection


class Group(FairscapeBaseModel, extra=Extra.allow):
    type = "Organization"
    owner: UserCompactView
    members: List[UserCompactView]


    def create(self, MongoCollection: Collection) -> OperationStatus:
        return super().create(MongoCollection)


    def read(self, MongoCollection: Collection) -> OperationStatus:
        # check permissions here
        return super().read(MongoCollection)


    def delete(self, MongoCollection: Collection) -> OperationStatus:
        # check that record exists

        # for all users who are members of this group
        # modify their user record 

        return self.super().create(MongoCollection)


    def update(self, MongoCollection: Collection) -> OperationStatus:
        return self.super().update(MongoCollection)

    
    def addUser(self, MongoCollection: Collection, Member) -> OperationStatus:

        pass

    def removeUser(self, MongoCollection: Collection, Member) -> OperationStatus:
        pass

