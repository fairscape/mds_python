from typing import List, Literal, Tuple
from pydantic import EmailStr, Extra
from mds.utils import FairscapeBaseModel, OrganizationCompactView, ProjectCompactView, DatasetCompactView, SoftwareCompactView, ComputationCompactView
import pymongo


class User(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["Person"]
    email: EmailStr  # requires installation of module email-validator
    password: str
    is_admin: bool
    organizations: List[OrganizationCompactView]
    projects: List[ProjectCompactView]
    datasets: List[DatasetCompactView]
    software: List[SoftwareCompactView]
    computations: List[ComputationCompactView]

  
    def create(self, MongoCollection: pymongo.collection.Collection) -> Tuple[bool, str, int]: 

        # creating a new user we must set their owned objects to none
        self.projects = []
        self.datasets = []
        self.software = []
        self.computations = []

        try: 
            create_request = MongoCollection.insert_one(self.json(by_alias=True))

            if create_request.acknowledged:
                return (True, "", 200)
            else:
                return (False, "", 200)

        except pymongo.errors.ConnectionError as e:
            return (False, f"MongoConnectionError: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return (False, f"Error: {str(e)}", 400)


    def read(self, MongoCollection) -> Tuple[bool, str, int]:

        try: 
            query = test_collection.find_one(
                {"@id": test_data["@id"]}, 
                projection={"_id": False}
                )
            
        except pymongo.errors.ConnectionFailure as e:
            return (False, f"MongoConnectionError: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return (False, f"Undetermined Error: {e}", 400)

        else:

            # check that the results are not empty
            if query:
                # update class with values from database
                for key, value in query.items():
                    setattr(self, key, value)
                return (True, "", 200)

            else:
                return (False, "No record found", 404)


    def delete(self, MongoCollection) -> Tuple[bool, str]:
        pass

    def update(self, MongoCollection) -> Tuple[bool, str]:
        pass



