from pydantic import BaseModel, Extra, validator, Field
from typing import List
from .utils import validate_ark, UserCompactView


class Group(BaseModel, extra=Extra.allow):
    id: str
    name: str
    owner: UserCompactView
    members: List[UserCompactView]

    _validate_guid = validator('id', allow_reuse=True)(validate_ark)
