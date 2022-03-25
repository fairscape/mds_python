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

        # check if the user already exists in the database
        if MongoCollection.find_one({"@id": self.id}):
            return (False, "document already exists", 400)

        try: 
            create_request = MongoCollection.insert_one(self.dict(by_alias=True))

            if create_request.acknowledged:
                return (True, "", 200)
            else:
                return (False, "", 400)


        except pymongo.errors.DuplicateKeyError as e:
            return (False, f"DuplicateKeyError: {str(e)}", 400)
        
        except pymongo.errors.WriteError as e:
            return (False, f"MongoWriteError: {str(e)}", 500)

        except pymongo.errors.ConnectionFailure as e:
            return (False, f"MongoConnectionError: {str(e)}", 500)

        # catch all exceptions
        except Exception as e:
            return (False, f"Error: {str(e)}", 500)


    def read(self, MongoCollection) -> Tuple[bool, str, int]:

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
                return (True, "", 200)

            else:
                return (False, "no record found", 404)
            
        except pymongo.errors.ConnectionFailure as e:
            return (False, f"MongoConnectionError: {str(e)}", 500)


        except pymongo.errors.ExecutionTimeout as e:
            return (False, f"MongoExecutionTimeoutError: {str(e)}", 500)


        # catch all exceptions
        except Exception as e:
            return (False, f"Undetermined Error: {e}", 500)


    def delete(self, MongoCollection) -> Tuple[bool, str, int]:


        full_user_query = MongoCollection.find_one({"@id": self.id}) 

        # make sure the user exists
        if full_user_query == None:
            return (False, "User not Found", 404)

        # check that user doesn't have any owned objects
        if MongoCollection.find_one({"owner": self.id}):
            return (False, "Cannot Delete User with Owned Objects", 400)

        # delete 
        MongoCollection.delete_one({"@id": self.id})
        return (True, "", 200)


    def update(self, MongoCollection) -> Tuple[bool, str, int]:
 
        new_values = {
            "$set":  {k: value for k,value in self.dict() if value != None}
        }

        result = MongoCollection.update_one({"@id": self.id}, new_values)

        return (True, "", 200)






