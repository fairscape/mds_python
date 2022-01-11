from pydantic import BaseModel, Extra
from typing import List

class UserView(BaseModel):
	id: str
	objectType = "Person" 
	name: str
	email: str

class Group(BaseModel, extra=Extra.allow):
	id: str
	name: str
	owner: UserView
	members: List[UserView]
