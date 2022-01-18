from pydantic import BaseModel, Extra, validator, ValidationError, root_validator
from typing import List
from .helpers import validate_ark


class UserView(BaseModel):
	id: str
	objectType = "Person" 
	name: str
	email: str

	_validate_guid = validator('id', allow_reuse=True)(validate_ark)

	@root_validator
	def check_valid_jsonld(cls, values):
		return values


class Group(BaseModel, extra=Extra.allow):
	id: str
	name: str
	owner: UserView
	members: List[UserView]

	_validate_guid = validator('id', allow_reuse=True)(validate_ark)