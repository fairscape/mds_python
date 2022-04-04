import re
from typing import Literal

from pydantic import BaseModel, validator


def validate_ark(guid: str) -> str:
    ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

    ark_matches = re.findall(ark_regex, guid)

    if len(ark_matches) != 1:
        raise ValueError(f"ark syntax error: {guid}")

    prefix, postfix = ark_matches[0]

    if len(postfix) == 0:
        raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

    return guid


def validate_email(email_str: str) -> str:
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    email_matches = re.findall(email_regex, email_str)

    if len(email_matches) != 1:
        raise ValueError(f"email syntax error: {email_str}")

    return email_str


class FairscapeBaseModel(BaseModel):
    id: str
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
    email: str

    _validate_email = validator('email', allow_reuse=True)(validate_email)


class SoftwareCompactView(FairscapeBaseModel):
    type: Literal["evi:Software"]


class DatasetCompactView(FairscapeBaseModel):
    type: Literal["evi:Dataset"]


class ComputationCompactView(FairscapeBaseModel):
    type: Literal["evi:Computation"]


class EvidenceGraphCompactView(FairscapeBaseModel):
    type: Literal["evi:EvidenceGraph"]


class OrganizationCompactView(FairscapeBaseModel):
    type: Literal["Organization"]


class ProjectCompactView(FairscapeBaseModel):
    type: Literal["Project"]


class DataDownloadCompactView(FairscapeBaseModel):
    type: Literal["DataDownload"]
