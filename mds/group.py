from pydantic import BaseModel

class UserView(BaseModel):
	id: str
	objectType = "Person" 
	name: str
	email: str

class Group(BaseModel):
	id: str
	name: str
	owner: UserView
	members: List[UserView]

	class Config:
		extra = allow
