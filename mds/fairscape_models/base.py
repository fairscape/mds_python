from pydantic import (
    BaseModel,
    constr,
    AnyUrl,
    Extra
)

from typing import Optional, Union, Dict, List
from pydantic import BaseModel, validator
import pymongo
from mds.utilities.operation_status import OperationStatus


class FairscapeBaseModel(BaseModel):
    guid: str
    context: Union[str, Dict[str,str]] = {
                "@vocab": "https://schema.org/",
                "evi": "https://w3id.org/EVI#"
            }
    metadataType: str    
    name: constr(max_length=64)

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True    
        fields={
            "context": {
                "title": "context",
                "alias": "@context"
            },
            "guid": {
                "title": "guid",
                "alias": "@id"
            },
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            },
            "name": {
                "title": "name"
            }
        }
    

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
            print("called")
            # run the query
            query = MongoCollection.find_one(
                {'@id': self.guid},
                projection=query_projection
            )
            print(self.dict(by_alias=True))
            # check that the results are no empty
            if query:
                # update class with values from database
                for k, value in query.items():
                    print('\n')
                    print(k, value)
                    if k[1] == '@':
                        self.k[1:] = value
                    #if not k == "distribution":
                    #    setattr(self.dict(by_alias=True), k, value)
                print(self)
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
