from typing import Optional, Union, Dict, List
from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)

from datetime import datetime

class Dataset(BaseModel):
    guid: str
    context: Union[str, Dict[str,str]] = {
                "@vocab": "https://schema.org/",
                "evi": "https://w3id.org/EVI#"
            }    
    name: constr(max_length=64)
    metadataType: str = "https://w3id.org/EVI#Dataset"
    author: constr(max_length=64)
    datePublished: str
    version: str
    description: constr(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str
    dataSchema: Optional[Union[str, dict]]
    generatedBy: Optional[List[str]]
    derivedFrom: Optional[List[str]]
    usedBy: Optional[List[str]]
    contentUrl: Optional[str]

    class Config:
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
            },
            "fileFormat": {
                "title": "fileFormat",
                "alias": "format"
            },
            "dataSchema": {
                "title": "dataSchema",
                "alias": "schema"
            }
        }
