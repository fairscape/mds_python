import re
from typing import Literal

from pydantic import BaseModel, validator, EmailStr


def validate_ark(guid: str) -> str:

	ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

	ark_matches = re.findall(ark_regex, guid)

	if len(ark_matches) != 1:
		raise ValueError(f"ark syntax error: {guid}")

	prefix, postfix = ark_matches[0]
	
	if len(postfix) == 0:
		raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

	return guid


class FairscapeBaseModel(BaseModel):
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


class UserCompactView(FairscapeBaseModel):
	type: Literal["Person"]
	email: EmailStr  


class SoftwareCompactView(FairscapeBaseModel):
	type: Literal["evi:Software"] 


class DatasetCompactView(FairscapeBaseModel):
	type: Literal["evi:Dataset"] 


class OrganizationCompactView(FairscapeBaseModel):
	type: Literal["Organization"]


class ComputationCompactView(FairscapeBaseModel):
	type: Literal["evi:Computation"]


class ProjectCompactView(FairscapeBaseModel):
	type: Literal["Project"]


class EvidenceGraphCompactView(FairscapeBaseModel):
	type: Literal["evi:EvidenceGraph"]
	#graph: str

	#class Config:
	#	fields = {
	#		"graph": {
	#			"title": "graph",
	#			"alias": "@graph"
	#		}
	#	}

