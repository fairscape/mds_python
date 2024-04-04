from typing import Optional
from pydantic import Extra
import re
from fairscape_mds.mds.models.fairscape_base import *
from fairscape_mds.mds.utilities.operation_status import OperationStatus

def listSchema(mongo_collection: pymongo.collection.Collection):
   
    user_cursor = mongo_collection.find(
        query={"@type": "evi:Schema"}, 
        projection={"@id": True, "name": True, "description": True}
        )
    

    pass



# DO I need this for schema?
def deleteUserByID(
    mongo_collection: pymongo.collection.Collection, 
    user_id: str
    )-> dict:
    ''' Delete a user by setting their account status to deactivated

    - TODO Preserves all their metadata.
    - TODO removes their ability to login
    - TODO in order to delete account all files must be given admin access to 
        another individual
    '''
    
    deleted_user = mongo_collection.find_one_and_delete({"@id": user_id})
    return deleted_user

def validate_type(cls, value):
    valid_types = {'integer', 'number', 'string', 'array','boolean'}
    if value is not None:
        if value not in valid_types:
            raise ValueError(f"Type must be one of {valid_types}")
    return value

class Property(BaseModel, extra = Extra.allow):
    description: str = Field(...)
    index: Union[str, int] = Field(...)
    type: str = Field(...)
    value_url: Optional[str] = Field(default = None, alias = 'value-url')
    pattern: Optional[str] = Field(default = None)
    items_datatype: Optional[str] = Field(default = None, alias = 'items-datatype')
    min_items: Optional[int] = Field(default = None, alias = 'min-items')
    max_items: Optional[int] = Field(default = None, alias = 'max-items')
    unique_items: Optional[bool] = Field(defaul = None, alias = 'unique-items')


    @validator('index')
    def validate_index(cls, value):
        if isinstance(value, str):
            # Allow something like int::int for index. Raise error if else
            pattern = r'^\d+$|^-?\d+::|^-?\d+::-?\d+$|^::-?\d+'
            if not re.match(pattern, value):
                raise ValueError("Index must match the pattern 'int::int'")
        return value
    
    _validate_type = validator('type','items-datatype', allow_reuse=True)(validate_type)

    @validator('pattern')
    def validate_pattern(cls, value):
        if value is not None:
            try:
                re.compile(value)
            except re.error:
                raise ValueError("Pattern must be a valid regular expression")
        return value

class Schema(FairscapeBaseModel, extra=Extra.allow):
    context: dict = Field( 
        default= {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context" 
    )
    metadataType: str = Field(alias="@type", default= "evi:Schema")
    properties: Dict[str:Property]

    def create(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # creating a new user we must set their owned objects to none
        self.projects = []
        self.datasets = []
        self.rocrates = []
        self.software = []
        self.computations = []
        self.evidencegraphs = []

        return super().create(MongoCollection)

    def read(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().read(MongoCollection)

    def update(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        return super().update(MongoCollection)

    def delete(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
        # TODO Make sure user doesn't have any owned resources
        return super().delete(MongoCollection)


def list_users(mongo_collection: pymongo.collection.Collection):
    cursor = mongo_collection.find(
        filter={"@type": "Person"},
        projection={"_id": False}
    )
    return {"users":  [{"@id": user.get("@id"), "@type": "Person", "name": user.get("name")} for user in cursor] }

