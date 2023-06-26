from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)

from typing import Optional, Union, Dict, List


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
