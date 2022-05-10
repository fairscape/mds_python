from mds.models.fairscape_base import *


class UserCompactView(FairscapeBaseModel):
    type = "Person"
    email: str

    validate_email = validator('email', allow_reuse=True)(validate_email)