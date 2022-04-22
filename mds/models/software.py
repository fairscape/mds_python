from pydantic import  Extra
from typing import List, Literal, Union
from .utils import FairscapeBaseModel, UserCompactView, ComputationCompactView


class Software(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type: Literal["evi:Software"]
    owner: UserCompactView
    author: Union[str, UserCompactView]
    downloadUrl: str
    citation: str
    usedBy: List[ComputationCompactView]

    class Config:
        extra = Extra.allow
        fields = {
            "usedBy": {
                "alias": "evi:usedBy"
            },
            "type": {
                "alias": "@type"
            }
        }


