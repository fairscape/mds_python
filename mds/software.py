from pydantic import BaseModel, Extra, validator, ValidationError, root_validator
from typing import List
from mds import UserView


class Software(BaseModel, extra=Extra.allow):
    id: str
    name: str
    owner: UserView
    author: str
    downloadUrl: str
    citation: str
    # evi:usedBy: List[Computation]


