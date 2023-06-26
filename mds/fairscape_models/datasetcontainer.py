from typing import Optional, Union, Dict, List

from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)
from datetime import datetime

class DatasetContainer(BaseModel):
    guid: str
    conformsTo: Union[str, Dict[str,str]] = {
                "@id": "https://w3id.org/ro/crate/1.1"
            }
    about: Union[str, Dict[str,str]] 
    isPartOf: Union[str, Dict[str,str]]     
    metadataType: Optional[str] = "https://w3id.org/EVI#Dataset"    
    contentUrl: Optional[str]

    class Config:
        fields={            
            "guid": {
                "title": "guid",
                "alias": "@id"
            },
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            }
        }
