from fastapi import Form
from pydantic import BaseModel

# Compatible with POST when sent via ajax requests
class SigninRequest(BaseModel):
    email: str
    password: str


class SignInForm(BaseModel):
    # must match with name="email" in the signin html form
    email: str
    # must match with name="password" in the signin html form
    password: str

    @classmethod
    def as_form(cls, email: str = Form(...), password: str = Form(...)):
        return cls(email=email, password=password)


