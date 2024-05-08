from pydantic import (
    BaseModel, 
    Field
    )


class AccessControlList(BaseModel):
    read: List[str] = Field(default=[])
    write: List[str] = Field(default=[])
    delete: List[str] = Field(default=[])
    update: List[str] = Field(default=[])

