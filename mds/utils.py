from pydantic import BaseModel, validator, Field, EmailStr
from typing import Literal, Optional, Tuple
import re
import pymongo


def validate_ark(guid: str) -> str:
    """
    Validate ark syntax and return the value of the passed string if correct, otherwise raise a ValueError exeption

    The current validation that occurs is as followed.
    The structure of an ark is broken into two parts, the prefix and the postfix.
    The prefix and the postfix are seperated by a single slash "/".
    The prefix must be start with "ark:" followed by 5 numbers.
    And the postfix can have any number of characters or digits and dashes are allowed.

    This function could  be improved to identify more aspects of ark structure
    i.e.
    According to the ark RFC
    ? may determine the type of content to return

    Parameters
    ----------
    guid: string to be validated

    Returns
    -------
    str: the value of the passed guid, only returned if validation succeeds

    """

    ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

    ark_matches = re.findall(ark_regex, guid)

    if len(ark_matches) != 1:
        raise ValueError(f"ark syntax error: {guid}")

    prefix, postfix = ark_matches[0]

    if len(postfix) == 0:
        raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

    return guid


class OperationStatus():

    def __init__(self, success: bool, message: str, status_code: int, error_type: str = None):
        self.success = success
        self.message = message
        self.status_code = status_code

        self.error_type = error_type

    def __str__(self):
        return f"Success: {self.success}\tMessage: {self.message}\tStatusCode: {self.status_code}"



class FairscapeBaseModel(BaseModel):
    id:   str
    type: str
    name: str

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True
        fields = {
                "id": {
                        "title": "id",
                        "alias": "@id",
                        },
                "type": {
                        "title": "type",
                        "alias": "@type",
                },
                "name": {
                        "title": "name",
                }
        }

    _validate_guid = validator('id', allow_reuse=True)(validate_ark)


    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """
        Persist instance of model in mongo

        This is the superclass method for create operations in fairscape.
        It will check that there is for collision for the @id, then attempt to

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection

        Returns
        -------
        mds.utils.OperationStatus
        """

        if MongoCollection.find_one({"@id": self.id}):
            return OperationStatus(False, "document already exists", 400)

        try:
            create_request = MongoCollection.insert_one(self.dict(by_alias=True))
            if create_request.acknowledged:
                return OperationStatus(True, "", 200)
            else:
                return OperationStatus(False, "", 400)

        except pymongo.errors.DuplicateKeyError as e:
            return OperationStatus(False, f"DuplicateKeyError: {str(e)}", 400)
        except pymongo.errors.WriteError as e:
            return OperationStatus(False, f"MongoWriteError: {str(e)}", 500)
        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"MongoConnectionError: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)


    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """
        Delete an instance of a model in mongo

        This is the superclass method for delete operations in fairscape.
        It will check that a document with @id exists in the database before deleting

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection

        Returns
        -------
        mds.utils.OperationStatus
        """

        full_user_query = MongoCollection.find_one({"@id": self.id})

        # make sure the object exists
        if full_user_query == None:
            return OperationStatus(False, "Object not Found", 404)

        # TODO check the output status
        MongoCollection.delete_one({"@id": self.id})
        return OperationStatus(True, "", 200)


    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """
        Update an instance of a model in mongo

        This is the superclass method for update operations in fairscape.
        It will check that a document with @id exists in the database before updating
        It will check the set properties and then preform the mongo replace operation.
        This is equivalent to an overwrite of the passed data properties.

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection

        Returns
        -------
        mds.utils.OperationStatus
        """

        if MongoCollection.find_one({"@id": self.id}):
            return OperationStatus(False, "object not found", 404)

        new_values = {
                "$set":  {k: value for k,value in self.dict() if value != None}
        }

        # TODO use result to check transaction success
        update_result = MongoCollection.update_one({"@id": self.id}, new_values)

        return OperationStatus(True, "", 200)


    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        """
        Read an instance of a model in mongo and unpack the values into the current fairscape base model attributes

        This is the superclass method for read operations in fairscape.

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection
        Returns
        -------
        mds.utils.OperationStatus
        """
        try:
            query = MongoCollection.find_one(
                    {"@id": self.id},
                    projection={"_id": False}
            )

            # check that the results are not empty
            if query:
                # update class with values from database
                for key, value in query.items():
                    setattr(self, key, value)
                return OperationStatus(True, "", 200)

            else:
                return OperationStatus(False, "no record found", 404)

        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"MongoConnectionError: {str(e)}", 500)
        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"MongoExecutionTimeoutError: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Undetermined Error: {e}", 500)


    def update_append(self, MongoCollection, Field: str, Item) -> OperationStatus:
        update_result = MongoCollection.update_one(
                {"@id": self.id},
                {"$push": {Field: Item.dict(by_alias=True)}}
        )
        return OperationStatus(True, "", 200)


    def update_remove(self, MongoCollection, Field: str, Item) -> OperationStatus:
        # use the $pull operator to check matching values
        update_result = MongoCollection.update_one(
                {"@id": self.id},
                {"$pull": {Field: Item.dict(by_alias=True)}}
        )

        return OperationStatus(True, "", 200)


class UserCompactView(FairscapeBaseModel):
    type = "Person"
    email: EmailStr


class SoftwareCompactView(FairscapeBaseModel):
    type = "evi:Software"


class DatasetCompactView(FairscapeBaseModel):
    type = "evi:Dataset"


class OrganizationCompactView(FairscapeBaseModel):
    type = "Organization"


class ComputationCompactView(FairscapeBaseModel):
    type = "evi:Computation"


class ProjectCompactView(FairscapeBaseModel):
    type = "Project"
