from typing import List

from pydantic import BaseModel, EmailStr

from mds import Software, Computation


class User(BaseModel):
    # type: 'Person'
    id: str
    name: str
    email: EmailStr  # requires installation of module email-validator
    password: str
    is_admin: bool
    # organizations: List[Organization]
    # projects: List[Project]
    # datasets: List[Dataset]
    software: List[Software]
    computations: List[Computation]
