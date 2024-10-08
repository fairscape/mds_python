from pydantic import (
    BaseModel, 
    Field
    )
from typing import List

class Permissions(BaseModel):
    owner: str
    group: str

class AccessControlList(BaseModel):
    owner: str
    read: List[str] = Field(default=[])
    write: List[str] = Field(default=[])
    delete: List[str] = Field(default=[])
    update: List[str] = Field(default=[])

