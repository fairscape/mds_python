from pydantic import Extra
from typing import List, Union, Literal
from datetime import datetime
from .utils import FairscapeBaseModel, OrganizationCompactView, UserCompactView, SoftwareCompactView, DatasetCompactView


class Computation(FairscapeBaseModel):
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
    type: Literal["evi:Computation"]
    owner: UserCompactView
    author: str
    dateCreated: datetime
    dateFinished: datetime
    associatedWith: List[Union[OrganizationCompactView, UserCompactView]]
    usedSoftware: List[SoftwareCompactView]
    usedDataset: List[DatasetCompactView]

    class Config:
        extra = Extra.allow
