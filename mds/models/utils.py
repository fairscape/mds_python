from pydantic import BaseModel, validator, Field, EmailStr
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
                "context": {
                    "title": "context",
                    "alias": "@context",
                    },
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


    def create(self, MongoCollection: pymongo.collection.Collection, bson = None) -> OperationStatus:
        """
        Persist instance of model in mongo

        This is the superclass method for create operations in fairscape.
        It will check that there is for collision for the @id, then attempt to

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection
        bson: A representation of the object using bson, allows for use of embedded document storage in Mongo

        Returns
        -------
        mds.utils.OperationStatus
        """

        # check if a bson representation is passed
        # if not use the pydantic aliasing
        if bson is None:
            insert_document = self.dict(by_alias=True)
        else:
            insert_document = bson

        try:

            if MongoCollection.find_one({"@id": self.id}):
                return OperationStatus(False, "document already exists", 400)


            create_request = MongoCollection.insert_one(insert_document)
            if create_request.acknowledged and create_request.inserted_id:
                return OperationStatus(True, "", 200)
            else:
                return OperationStatus(False, "", 400)

        # write specific exception handling
        except pymongo.errors.DocumentTooLarge as e:
            return OperationStatus(False, f"Mongo Error Document Too Large: {str(e)}", 500)

        except pymongo.errors.DuplicateKeyError as e:
            return OperationStatus(False, f"Mongo Duplicate Key Error: {str(e)}", 500)
  
        except pymongo.errors.WriteError as e:
            return OperationStatus(False, f"Mongo Write Error: {str(e)}", 500)

        # default exceptions for all mongo operations
        except pymongo.errors.ConnectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        except pymongo.errors.ConnectionError as e:
            return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)
        
        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Error Invalid Name: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Error Network Timeout: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)
        

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

        try:

            # make sure the object exists
            # if it doesn't return a 404
            if MongoCollection.find_one({"@id": self.id}) is None:
                return OperationStatus(False, "Object not Found", 404)

            # preform the delete one operation
            delete_result = MongoCollection.delete_one({"@id": self.id})

            # if the transaction is successfull, return a successfull OperationStatus
            if delete_result.acknowledged and delete_result.deleted_count == 1:
                return OperationStatus(True, "", 200)
            else:
            # otherwise return the string of the error
                return OperationStatus(False, f"Delete Error: {str(delete_result)}", 400)
                
        # default exceptions for all mongo operations
        except pymongo.errors.ConnectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        except pymongo.errors.ConnectionError as e:
            return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)
        
        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Error Invalid Name: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Error Network Timeout: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)


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

        try: 

            new_values = {
                    "$set":  {k: value for k,value in self.dict() if value != None}
            }

            update_result = MongoCollection.update_one({"@id": self.id}, new_values)

            if update_result.acknowledged and update_result.modified_count == 1:
                return OperationStatus(True, "", 200)
            
            if update_result.matched_count == 0:
                return OperationStatus(False, "object not found", 404)

            else:
                return OperationStatus(False, "", 500)

        # update specific mongo exceptions
        except pymongo.errors.DocumentTooLarge as e:
            return OperationStatus(False, f"Mongo Error Document Too Large: {str(e)}", 500)

        except pymongo.errors.DuplicateKeyError as e:
            return OperationStatus(False, f"Mongo Duplicate Key Error: {str(e)}", 500)
  
        except pymongo.errors.WriteError as e:
            return OperationStatus(False, f"Mongo Write Error: {str(e)}", 500)

        # default exceptions for all mongo operations
        except pymongo.errors.ConnectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        except pymongo.errors.ConnectionError as e:
            return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)
        
        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Error Invalid Name: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Error Network Timeout: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)



    def read(self, MongoCollection: pymongo.collection.Collection, exclude: list[str] = None) -> OperationStatus:
        """
        Read an instance of a model in mongo and unpack the values into the current  
        FairscapeBaseModel attributes

        This is the superclass method for read operations in fairscape.

        Parameters
        ----------
        self : FairscapeBaseModel
        MongoCollection : pymongo.collection.Collection
        exclude: list[str] a list of field names to exclude from the returned document
        Returns
        -------
        mds.utils.OperationStatus
        """

        # given passed list of fields to exclude from query
        # form the projection argument to the find_one mongo command
        if exclude:
            query_projection ={excluded_field: False for excluded_field in exclude}
            query_projection["_id"] = False
        else:
            query_projection = {"_id": False}

        try:
            # run the query
            query = MongoCollection.find_one(
                    {"@id": self.id},
                    projection= query_projection
            )

            # check that the results are not empty
            if query:
                # update class with values from database
                for key, value in query.items():       
                    setattr(self, key, value)
                return OperationStatus(True, "", 200)

            else:
                return OperationStatus(False, "no record found", 404)

        # default exceptions for all mongo operations
        except pymongo.errors.ConnectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        except pymongo.errors.ConnectionError as e:
            return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)
        
        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Error Invalid Name: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Error Network Timeout: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)
        

        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)


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
