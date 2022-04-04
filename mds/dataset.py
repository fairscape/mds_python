from typing import Literal, Union
from datetime import datetime
from mds.utils import FairscapeBaseModel, UserCompactView, ProjectCompactView, OrganizationCompactView


class Dataset(FairscapeBaseModel):
    type: Literal["evi:Dataset"]
    owner: UserCompactView
    includedInDataCatalog: ProjectCompactView
    sourceOrganization: OrganizationCompactView
    distribution: str
    author: Union[str, UserCompactView]
    dateCreated: datetime
    dateModified: datetime
