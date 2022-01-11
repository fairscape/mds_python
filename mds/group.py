from pydantic import BaseModel, Extra, validator, ValidationError
from typing import List

class UserView(BaseModel):
	id: str
	objectType = "Person" 
	name: str
	email: str

	@validator('id')
	def id_ark_format(cls, v):
		if 'ark:' not in v:
			raise ValueError(f"ark: prefix not in identifier {v}")
		return v

class Group(BaseModel, extra=Extra.allow):
	id: str
	name: str
	owner: UserView
	members: List[UserView]
