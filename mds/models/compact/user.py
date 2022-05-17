from mds.models.fairscape_base import *
from mds.utilities.utils import validate_email


class UserCompactView(FairscapeBaseModel):
    type = "Person"
    email: str

    validate_email = validator('email', allow_reuse=True)(validate_email)