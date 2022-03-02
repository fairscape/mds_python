from pydantic import BaseModel, Extra, validator, ValidationError, root_validator
from typing import List, Union
from mds import Software, UserView
from pydantic.types import date


class Computation(BaseModel, extra=Extra.allow):
    id: str
    name: str
    owner: UserView
    author: str
    dateCreated: date
    dateFinished: date
    # associatedWith: Union[Organization, Person]
    usedSoftware: List[Software]
    # usedDataset: List[Dataset]
