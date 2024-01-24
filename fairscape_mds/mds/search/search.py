from mds.config import (
    get_mongo 
)
from pydantic import BaseModel, ValidationError
from enum import Enum


class TypeEnum(str, enum):
    dataset = "Dataset"
    user = "Person"
    organization = "Organization"
    project = "Project"
    software = "Software"
    computation = "Computation"
    download = "DataDownload" 
    rocrate = "ROCrate"
    

class SearchRequest(BaseModel):
    entityType: Union[TypeEnum, None] = None
    textSearch: Optional[str] = None
    name: Optional[str] = None
    nameContains: Optional[str] = None
    descriptionContains: Optional[str] = None
    isPartOfOrganizationGUID: Optional[str] = None
    isPartOfProjectGUID: Optional[str] = None
    isPartOfROCrateGUID: Optional[str] = None
    dataInFairscape: Optional[bool] = None
    dataSizeGreaterThan: Optional[int] = None
    dataSizeLessThan: Optional[int] = None
    datatype: Optional[str] = None
    
   

    def ReturnQuery(self) -> dict: 
        mongo_query = {'$and': []}

        def if_not_none(attribute, query_text):
            if attribute is not None:
                mongo_query['$and'].append(query_text)

        # query for 
        if_not_none(self.entityType, self.typeQuery())

        # text search
        if_not_none(
            self.textSearch,
            {
                "$text": {
                    "$search": self.textSearch
                }
            }
        )
        
        # name match
        if_not_none(
            self.name, 
            {
                "name": {"$eq": self.name}
            }
        )
        
        # name contains
        if_not_none(
            self.nameContains, 
            {
                "name": {
                    "$regex": self.nameContains
                }
            }
        )

        # description contains
        if_not_none(
            self.description, 
            {
                "description": {
                    "$regex": self.description
                }
            }     
        )
             

        # dataInFairscape
        #if_not_none(self.dataInFairscape, self.inFairscapeQuery)

        # dataSizeGreaterThan
        #if_not_none(self.dataSizeGreaterThan, self.dataSizeGreaterThanQuery)

        # dataSizeLessThan
        #if_not_none(self.dataSizeLessThan, self.dataSizeGreaterThanQuery)

        # dataMIMETYPE
        return mongo_query


    def typeQuery(self) -> dict:
        # query for @type        
        if self.entityType == TypeEnum.dataset:
            return {
               "@type": "evi:Dataset"
            }
        elif self.entityType == TypeEnum.user:
            return {
                "@type": "Person"
            }
        elif self.entityType == TypeEnum.organization:
            return {
                "@type": "Organization"
            }
        elif self.entityType == TypeEnum.software:
            return {
                "@type": "evi:Software"
            }
        elif self.entityType == TypeEnum.download:
            return {
                "@type": "DataDownload"
            }
        elif self.entityType == TypeEnum.computation:
            return {
                "@type": "evi:Computation"
            }
        elif self.entityType == TypeEnum.project:
            return {
                "@type": "Project"
            } 




