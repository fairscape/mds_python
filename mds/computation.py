from pydantic import Extra
from typing import List, Union
from pydantic.types import date
from mds.utils import FairscapeBaseModel, OrganizationCompactView, UserCompactView, SoftwareCompactView, DatasetCompactView


class Computation(FairscapeBaseModel, extra=Extra.allow):
    id: str
    name: str
    owner: UserCompactView
    author: str
    dateCreated: date
    dateFinished: date
    associatedWith: List[Union[OrganizationCompactView, UserCompactView]]
    usedSoftware: List[SoftwareCompactView]
    usedDataset: List[DatasetCompactView]
