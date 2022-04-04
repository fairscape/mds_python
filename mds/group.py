from pydantic import Extra
from typing import List, Literal
from mds.utils import FairscapeBaseModel, UserCompactView


class Group(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["Organization"]
    owner: UserCompactView
    members: List[UserCompactView]
