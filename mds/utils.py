from pydantic import BaseModel, validator, Field, EmailStr
from typing import Literal, Optional
import re

def validate_ark(guid: str) -> str:

	ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

	ark_matches = re.findall(ark_regex, guid)

	if len(ark_matches) != 1:
		raise ValueError(f"ark syntax error: {guid}")

	prefix, postfix = ark_matches[0]
	
	if len(postfix) == 0:
		raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

	return guid


class CompactView(BaseModel):
	id:   str 
	type: str
	name: str

	class Config:
		allow_population_by_field_name = True
		validate_assignment = True
		fields = {
			"id": {
				"title": "id",
				"alias": "@id",
				},
			"type": {
				"title": "type",
				"alias": "@type",
			},
			"name": {
				"title": "name",
			}
		}

	_validate_guid = validator('id', allow_reuse=True)(validate_ark)




class UserCompactView(CompactView):
	type: Literal["Person"]
	email: EmailStr  

	# Haven't figured out how to default values
	# This only works for optional values
	# i.e. Optional[str]
	#@validator("type", pre=True, always=True)
	#def set_type(cls, type):
	#	return type or "Person"

	#class Config:
	#	fields = {
	#		"type": {
	#			"default": "Person"
	#		}
	#	}

	


class SoftwareCompactView(CompactView):
	type: Literal["evi:Software"] 


class DatasetCompactView(CompactView):
	type: Literal["evi:Dataset"] 




