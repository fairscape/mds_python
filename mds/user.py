from typing import List, Literal
from pydantic import EmailStr, Extra
from mds.utils import FairscapeBaseModel, OrganizationCompactView, ProjectCompactView, DatasetCompactView, SoftwareCompactView, ComputationCompactView


class User(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["Person"]
    email: EmailStr  # requires installation of module email-validator
    password: str
    is_admin: bool
    organizations: List[OrganizationCompactView]
    projects: List[ProjectCompactView]
    datasets: List[DatasetCompactView]
    software: List[SoftwareCompactView]
    computations: List[ComputationCompactView]
