from typing import Literal, List, Union
from mds.utils import FairscapeBaseModel, UserCompactView, ProjectCompactView


class Organization(FairscapeBaseModel):
    type: Literal["Organization"]
    owner: UserCompactView
    projects: List[ProjectCompactView]
