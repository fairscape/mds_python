from pydantic import Extra
from typing import List
from mds.utils import FairscapeBaseModel, UserCompactView


class Group(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["Organization"]
    owner: UserCompactView
    members: List[UserCompactView]