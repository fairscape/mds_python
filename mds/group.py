from pydantic import BaseModel, Extra, validator, ValidationError
from typing import List

def validate_ark(guid: str) -> str:
	if 'ark:' not in guid:
		raise ValueError(f"ark: prefix not in identifier {guid}")
	return guid


class UserView(BaseModel):
	id: str
	objectType = "Person" 
	name: str
	email: str

	_validate_guid = validator('id', allow_reuse=True)(validate_ark)


class Group(BaseModel, extra=Extra.allow):
	id: str
	name: str
	owner: UserView
	members: List[UserView]

	_validate_guid = validator('id', allow_reuse=True)(validate_ark)