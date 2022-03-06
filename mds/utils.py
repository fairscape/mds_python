from pydantic import BaseModel, validator, Field, EmailStr
from typing import Literal
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
	id: Field(str, alias="@id")
	type: Field(str, alias="@type")
	name: str
	_validate_guid = validator('id', allow_reuse=True)(validate_ark)


class UserCompactView(CompactView):
	type: Field(str, alias="@type") = Literal["Person"]
	email: EmailStr  # requires installation of module email-validator


class SoftwareCompactView(CompactView):
	type: Field(str, alias="@type") = Literal["evi:Software"]


class DatasetCompactView(CompactView):
	type: Field(str, alias="@type") = Literal["evi:Dataset"]




