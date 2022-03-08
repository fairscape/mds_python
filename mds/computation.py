from pydantic import Extra
from typing import List, Union, Computation
from pydantic.types import date
from mds.utils import FairscapeBaseModel, OrganizationCompactView, UserCompactView, SoftwareCompactView, DatasetCompactView


class Computation(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["evi:Computation"]
    owner: UserCompactView
    author: str
    dateCreated: date
    dateFinished: date
    associatedWith: List[Union[OrganizationCompactView, UserCompactView]]
    usedSoftware: List[SoftwareCompactView]
    usedDataset: List[DatasetCompactView]
