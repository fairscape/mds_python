from pydantic import (
    BaseModel, 
    validator,
    ConfigDict,
    Field,
    constr,
    Extra,
    computed_field
)
from typing import (
    List,
    Optional,
    Dict,
    Union
)
import pymongo
from fairscape_mds.mds.utilities.utils import validate_ark
from fairscape_mds.mds.utilities.operation_status import OperationStatus

ARK_NAAN = "59852"
IdentifierPattern = "ark[0-9]{5}\/.*"
DEFAULT_LICENSE = " https://creativecommons.org/licenses/by/4.0/"

default_context = {
    "@vocab": "https://schema.org/",
    "evi": "https://w3id.org/EVI#"
}


class Identifier(BaseModel):
    guid: str = Field(
        title="guid",
        alias="@id"
    )
    metadataType: str = Field(
        title="metadataType",
        alias="@type"
    )
    name: str


class FairscapeBaseModel(BaseModel, extra='allow'):
    """Refers to the Fairscape BaseModel inherited from Pydantic

    Args:
        BaseModel (Default Pydantic): Every instance of the Fairscape BaseModel must contain
        an id, a type, and a name
    """
    id: str = Field(None, alias="@id")
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
    )
    context: Dict[str, str] = Field(
        default=default_context,
        title="context",
        alias="@context"
    )
    metadataType: str = Field(
        title="metadataType",
        alias="@type"
    )
    url: Optional[str] = Field(default=None)
    name: str = Field(max_length=200)
    keywords: List[str] = Field(default=[])
    description: str = Field(min_length=5)
    license: Optional[str] = Field(default=DEFAULT_LICENSE)


    #@computed_field(alias="@id")
    #@property
    def generate_guid(self) -> str:
        # TODO url encode values
        # TODO add random hash digest

        # if
        return f"ark:{ARK_NAAN}/rocrate-{self.name.replace(' ', '')}"

    def create(self, MongoCollection: pymongo.collection.Collection, bson=None) -> OperationStatus:
        """Persist instance of model in mongo

        This is the superclass method for create operations in fairscape.
        It will check for collision of the submitted @id, then attempt to insert it into the collection.

        Args:
            MongoCollection (pymongo.collection.Collection): Collection which may contain instance of FairscapeBaseModel
            bson (None): A representation of the object using bson, allows for use of embedded document storage in Mongo

        Returns:
            OperationStatus: containing success, message, status code and error type (Default to None)
        """

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
            return OperationStatus(False, f"Mongo Document Too Large Error: {str(e)}", 500)

        except pymongo.errors.DuplicateKeyError as e:
            return OperationStatus(False, f"Mongo Duplicate Key Error: {str(e)}", 500)

        except pymongo.errors.WriteError as e:
            return OperationStatus(False, f"Mongo Write Error: {str(e)}", 500)

        # default exceptions for all mongo operations
        except pymongo.errors.CollectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid Error: {str(e)}", 500)

        # except pymongo.errors.ConnectionError as e:
        #    return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)

        except pymongo.errors.ConnectionFailure as e:
            return OperationStatus(False, f"Mongo Connection Failure Error: {str(e)}", 500)

        except pymongo.errors.ExecutionTimeout as e:
            return OperationStatus(False, f"Mongo Execution Timeout Error: {str(e)}", 500)

        except pymongo.errors.InvalidName as e:
            return OperationStatus(False, f"Mongo Invalid Name Error: {str(e)}", 500)

        except pymongo.errors.NetworkTimeout as e:
            return OperationStatus(False, f"Mongo Network Timeout Error: {str(e)}", 500)

        except pymongo.errors.OperationFailure as e:
            return OperationStatus(False, f"Mongo Error Operation Failure: {str(e)}", 500)


        # catch all exceptions
        except Exception as e:
            return OperationStatus(False, f"Error: {str(e)}", 500)

    def read(self, MongoCollection: pymongo.collection.Collection, exclude: List[str] = None) -> OperationStatus:
        """Read an instance of a model in mongo and unpack the values into the current
        FairscapeBaseModel attributes

        This is the superclass method for read operations in fairscape.

        Args:
            MongoCollection (pymongo.collection.Collection): Collection which may contain instance of FairscapeBaseModel
            exclude (List[str], optional): a list of field names to exclude from the returned document. Defaults to None.

        Returns:
            OperationStatus: containing success, message, status code and error type (Default to None)
        """

        # given passed list of fields to exclude from query
        # form the projection argument to the find_one mongo command
        if exclude:
            query_projection = {excluded_field: False for excluded_field in exclude}
            query_projection['_id'] = False
        else:
            query_projection = {'_id': False}

        try:
            # run the query
            query = MongoCollection.find_one(
                {'@id': self.id},
                projection=query_projection
            )

            # check that the results are no empty
            if query:
                # update class with values from database
                for k, value in query.items():
                    setattr(self, k, value)
                return OperationStatus(True, "", 200)
            else:
                return OperationStatus(False, "No record found", 404)

        # default exceptions for all mongo operations
        except pymongo.errors.CollectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        # except pymongo.errors.ConnectionError as e:
        #    return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)

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
        """Update an instance of a model in mongo

        This is the superclass method for update operations in fairscape.
        It will check that a document with @id exists in the database before updating
        It will check the set properties and then preform the mongo replace operation.
        This is equivalent to an overwrite of the passed data properties.

        Args:
            MongoCollection (pymongo.collection.Collection): Collection which may contain instance of FairscapeBaseModel

        Returns:
            OperationStatus: containing success, message, status code and error type (Default to None)
        """

        try:

            new_values = {
                "$set":
                    {k: value for k, value in self.dict(by_alias=True).items() if value is not None}
            }

            update_result = MongoCollection.update_one({"@id": self.id}, new_values)

            if update_result.acknowledged and update_result.modified_count == 1:
                return OperationStatus(True, "", 200)

            if update_result.matched_count == 0:
                return OperationStatus(False, "object not found", 404)


            else:
                return OperationStatus(False, "", 500)


        # update-specific mongo exceptions
        except pymongo.errors.DocumentTooLarge as e:
            return OperationStatus(False, f"Mongo Error Document Too Large: {str(e)}", 500)

        except pymongo.errors.DuplicateKeyError as e:
            return OperationStatus(False, f"Mongo Duplicate Key Error: {str(e)}", 500)

        except pymongo.errors.WriteError as e:
            return OperationStatus(False, f"Mongo Write Error: {str(e)}", 500)

        # default exceptions for all mongo operations
        except pymongo.errors.CollectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        # except pymongo.errors.ConnectionError as e:
        #    return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)

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
        """Delete an instance of a model in mongo

        This is the superclass method for delete operations in fairscape.
        It will check that a document with @id exists in the database before deleting

        Args:
            MongoCollection (pymongo.collection.Collection): Collection which may contain instance of FairscapeBaseModel

        Returns:
            OperationStatus: containing success, message, status code and error type (Default to None)
        """

        try:
            # make sure the object exists, return 404 otherwise
            if MongoCollection.find_one({"@id": self.id}) is None:
                return OperationStatus(False, "Object not found", 404)

            # perform delete one operation
            delete_result = MongoCollection.delete_one({"@id": self.id})

            # if deletion is successful, return success message
            if delete_result.acknowledged and delete_result.deleted_count == 1:
                return OperationStatus(True, "", 200)

            else:
                return OperationStatus(False, f"delete error: str({delete_result})", 404)


        # default exceptions for all mongo operations
        except pymongo.errors.CollectionInvalid as e:
            return OperationStatus(False, f"Mongo Connection Invalid: {str(e)}", 500)

        # except pymongo.errors.ConnectionError as e:
        #    return OperationStatus(False, f"Mongo Connection Error: {str(e)}", 500)

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

        # TODO read update result output to determine success
        update_result = MongoCollection.update_one(
            {"@id": self.id},
            {"$addToSet": {Field: Item}}
        )

        return OperationStatus(True, "", 200)


    def update_remove(self, MongoCollection, field: str, item_id: str) -> OperationStatus:
        """
        update_remove

        Updates a document removing an element from a list where the item matches a member on the field '@id'

        Parameters
        - self: FairscapeBaseClass
        - MongoCollection
        - Field: str
        - Item
        """

        # TODO read update result output to determine success
        update_result = MongoCollection.update_one(
            {"@id": self.id},
            {"$pull": {field:  {"@id": item_id} }}
        )

        return OperationStatus(True, "", 200)
